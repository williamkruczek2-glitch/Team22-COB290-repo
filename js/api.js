/*
 * api.js — the "backend" for R02 (manager dashboard) and R09 (insights).
 *
 * Part 1: functions read MIA.db (mock data) and do the calculations here.
 * Part 2: keep the same function names and return shapes, but replace each
 *         body with a fetch() to the endpoint noted above it. Pages never
 *         touch MIA.db directly, so nothing else has to change.
 *
 * Every function returns a Promise so the pages already behave as if the
 * data is coming over the network.
 */
var MIA = window.MIA || {};

MIA.config = {
  MIN_GROUP: 3,              // R10: never show a figure built from fewer people than this
  ON_TRACK_GAP: -5,          // progress gap (pts) still counted as on track
  AT_RISK_GAP: -15,          // gap at or below this = at risk
  ASSUMED_ALLOCATION: 0.5,   // share of each member's time on one project (awaiting client answer)
  TRAINING_FLAG: 0.40,       // issue rate that triggers "training suggested"
  TRAINING_WATCH: 0.25       // issue rate that triggers "keep an eye on"
};

MIA.api = (function (db, cfg) {
  var DAY = 86400000;
  var today = new Date(db.today);
  var date = function (s) { return new Date(s); };
  var isOpen = function (t) { return t.status !== 'done'; };
  var isOverdue = function (t) { return isOpen(t) && date(t.dueDate) < today; };
  var reply = function (data) { return Promise.resolve(JSON.parse(JSON.stringify(data))); };
  var byId = function (arr) { var m = {}; arr.forEach(function (x) { m[x.id] = x; }); return m; };
  var emp = byId(db.employees), team = byId(db.teams);
  var tasksOf = function (pid) { return db.tasks.filter(function (t) { return t.projectId === pid; }); };

  function workingDaysBetween(a, b) {
    var n = 0, cur = new Date(a);
    while (cur < b) { var day = cur.getDay(); if (day !== 0 && day !== 6) n++; cur = new Date(cur.getTime() + DAY); }
    return n;
  }

  // ---------- shared calculation: one project's health ----------
  function summarise(p) {
    var ts = tasksOf(p.id);
    var total = ts.length;
    var done = ts.filter(function (t) { return t.status === 'done'; }).length;
    var dueByNow = ts.filter(function (t) { return date(t.dueDate) <= today; }).length;
    var overdue = ts.filter(isOverdue).length;
    var blocked = ts.filter(function (t) { return t.status === 'blocked'; }).length;
    var pct = total ? Math.round((done / total) * 100) : 0;
    var expected = total ? Math.round((dueByNow / total) * 100) : 0;   // planned progress by today
    var gap = pct - expected;
    var end = date(p.endDate);
    var daysLeft = Math.round((end - today) / DAY);
    var status;
    if (pct === 100) status = 'complete';
    else if (daysLeft < 0 || gap <= cfg.AT_RISK_GAP) status = 'at_risk';
    else if (gap < cfg.ON_TRACK_GAP) status = 'behind';
    else status = 'on_track';

    return {
      id: p.id, code: p.code, name: p.name, description: p.description,
      manager: emp[p.managerId].name, team: team[p.teamId].name,
      startDate: p.startDate, endDate: p.endDate, daysLeft: daysLeft,
      memberCount: p.memberIds.length,
      totals: { total: total, done: done, open: total - done, overdue: overdue, blocked: blocked },
      progress: { actual: pct, expected: expected, gap: gap },
      status: status
    };
  }

  // ======================= R02 — Manager's dashboard =======================

  // Part 2: GET /api/managers/{managerId}/projects
  function getManagerProjects(managerId) {
    var mine = db.projects.filter(function (p) { return p.managerId === managerId; });
    return reply(mine.map(summarise));
  }

  // Part 2: GET /api/projects/{projectId}
  function getProjectDetail(projectId) {
    var p = db.projects.filter(function (x) { return x.id === projectId; })[0];
    if (!p) return Promise.reject(new Error('No project with ID ' + projectId));
    var ts = tasksOf(p.id);
    var summary = summarise(p);

    var byStatus = ['todo', 'in_progress', 'blocked', 'done'].map(function (s) {
      return { status: s, count: ts.filter(function (t) { return t.status === s; }).length };
    });

    // Burn-up: weekly planned (tasks due) vs actual (tasks done), start -> today
    var start = date(p.startDate), stop = date(p.endDate) < today ? date(p.endDate) : today;
    var points = [];
    for (var cur = start; cur <= stop; cur = new Date(cur.getTime() + 7 * DAY)) {
      points.push(weekPoint(ts, cur));
    }
    if (!points.length || points[points.length - 1].date !== db.today && stop.getTime() === today.getTime()) {
      points.push(weekPoint(ts, today));
    }

    var overdueTasks = ts.filter(isOverdue)
      .sort(function (a, b) { return date(a.dueDate) - date(b.dueDate); })
      .map(taskView);
    var upcoming = ts.filter(function (t) {
      var due = date(t.dueDate); return isOpen(t) && due >= today && due - today <= 14 * DAY;
    }).sort(function (a, b) { return date(a.dueDate) - date(b.dueDate); }).map(taskView);

    summary.byStatus = byStatus;
    summary.burnup = points;
    summary.overdueTasks = overdueTasks;
    summary.upcomingTasks = upcoming;
    return reply(summary);
  }

  function weekPoint(ts, when) {
    return {
      date: when.toISOString().slice(0, 10),
      planned: ts.filter(function (t) { return date(t.dueDate) <= when; }).length,
      actual: ts.filter(function (t) { return t.completedDate && date(t.completedDate) <= when; }).length
    };
  }

  function taskView(t) {
    return { id: t.id, title: t.title, area: t.area, status: t.status, priority: t.priority,
      dueDate: t.dueDate, assignee: emp[t.assigneeId].name,
      daysOverdue: Math.max(0, Math.round((today - date(t.dueDate)) / DAY)) };
  }

  // ======================= R09 — Organisation insights =======================
  // R10 rule: these figures are about teams, projects and skill areas — never
  // named people. Any group smaller than MIN_GROUP is withheld.

  // Part 2: GET /api/insights?teamId={teamId|all}
  function getInsights(teamId) {
    var all = teamId === 'all' || !teamId;
    var projs = db.projects.filter(function (p) { return all || p.teamId === teamId; });
    var pids = projs.map(function (p) { return p.id; });
    var ts = db.tasks.filter(function (t) { return pids.indexOf(t.projectId) !== -1; });
    var people = db.employees.filter(function (e) { return all || e.teamId === teamId; });

    return reply({
      scope: all ? 'All teams' : team[teamId].name,
      allocation: allocation(people),
      progress: projs.map(summarise),
      resourcing: projs.map(resourcing),
      training: training(ts)
    });
  }

  // Task allocation: how many people hold 0-2, 3-5, 6-8, 9+ open tasks.
  function allocation(people) {
    var buckets = [
      { label: '0–2', min: 0, max: 2, people: 0 }, { label: '3–5', min: 3, max: 5, people: 0 },
      { label: '6–8', min: 6, max: 8, people: 0 }, { label: '9+', min: 9, max: Infinity, people: 0 }
    ];
    var loads = people.map(function (e) {
      return db.tasks.filter(function (t) { return t.assigneeId === e.id && isOpen(t); }).length;
    });
    loads.forEach(function (n) {
      buckets.forEach(function (b) { if (n >= b.min && n <= b.max) b.people++; });
    });
    if (loads.length < cfg.MIN_GROUP) {
      return { suppressed: true, headcount: loads.length };
    }
    var sorted = loads.slice().sort(function (a, b) { return b - a; });
    var totalOpen = sorted.reduce(function (s, n) { return s + n; }, 0);
    // Smallest share of people holding half of all open tasks
    var acc = 0, k = 0;
    while (k < sorted.length && acc < totalOpen / 2) { acc += sorted[k]; k++; }
    var mean = totalOpen / loads.length;
    return {
      suppressed: false, headcount: loads.length, totalOpen: totalOpen,
      average: Math.round(mean * 10) / 10,
      halfHeldByPct: totalOpen ? Math.round((k / loads.length) * 100) : 0,
      buckets: buckets.map(function (b) { return { label: b.label, people: b.people }; })
    };
  }

  // Resourcing: open work (task-days) vs capacity left before the deadline.
  function resourcing(p) {
    var open = tasksOf(p.id).filter(isOpen);
    var demand = open.reduce(function (s, t) { return s + t.estimateDays; }, 0);
    var end = date(p.endDate);
    var daysLeft = end > today ? workingDaysBetween(today, end) : 0;
    var capacity = p.memberIds.length * daysLeft * cfg.ASSUMED_ALLOCATION;
    var ratio = capacity ? Math.round((demand / capacity) * 100) / 100 : null;
    var level = ratio === null ? (demand ? 'critical' : 'good')
      : ratio > 1 ? 'critical' : ratio > 0.8 ? 'warning' : 'good';
    var blocked = open.filter(function (t) { return t.status === 'blocked'; });
    return {
      id: p.id, name: p.name, demandDays: demand, capacityDays: Math.round(capacity),
      workingDaysLeft: daysLeft, ratio: ratio, level: level,
      pastDeadline: end < today, blocked: blocked.length
    };
  }

  // Training needs: per skill area, share of tasks that finished late,
  // were reopened, or are overdue now.
  function training(ts) {
    return db.areas.map(function (area) {
      var at = ts.filter(function (t) { return t.area === area; });
      var people = {};
      at.forEach(function (t) { people[t.assigneeId] = true; });
      var headcount = Object.keys(people).length;
      if (!at.length) return null;
      if (headcount < cfg.MIN_GROUP) return { area: area, suppressed: true, tasks: at.length };
      var late = at.filter(function (t) { return t.completedDate && date(t.completedDate) > date(t.dueDate); }).length;
      var reopened = at.filter(function (t) { return t.reopened; }).length;
      var overdue = at.filter(isOverdue).length;
      var issues = at.filter(function (t) {
        return t.reopened || isOverdue(t) || (t.completedDate && date(t.completedDate) > date(t.dueDate));
      }).length;
      var rate = issues / at.length;
      return {
        area: area, suppressed: false, tasks: at.length, people: headcount,
        late: late, reopened: reopened, overdue: overdue,
        issueRate: Math.round(rate * 100),
        level: rate >= cfg.TRAINING_FLAG ? 'critical' : rate >= cfg.TRAINING_WATCH ? 'warning' : 'good'
      };
    }).filter(Boolean).sort(function (a, b) { return (b.issueRate || -1) - (a.issueRate || -1); });
  }

  // Part 2: GET /api/teams
  function getTeams() { return reply(db.teams); }

  return {
    getManagerProjects: getManagerProjects,
    getProjectDetail: getProjectDetail,
    getInsights: getInsights,
    getTeams: getTeams
  };
})(MIA.db, MIA.config);

window.MIA = MIA;
