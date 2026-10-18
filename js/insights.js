/*
 * insights.js — R09: organisation insights.
 * Answers the four questions in the client letter:
 *   1. How well are tasks allocated?
 *   2. How well are projects progressing overall?
 *   3. Are projects resourced to finish in reasonable time?
 *   4. Where should training be provided?
 * R10: every figure is about teams, projects or skill areas, never a named
 * person, and groups smaller than MIA.config.MIN_GROUP are withheld.
 */



(function (api, ui, charts, session, cfg) {
  ui.renderNav('insights');
  var root = document.getElementById('insights');
  var teamSel = document.getElementById('team');

  if (!session.isManager()) {
    root.innerHTML = '<p class="notice">Insights are for managers and team leaders.</p>';
    document.querySelector('.filters').hidden = true;
    return;
  }

  api.getTeams().then(function (teams) {
    teamSel.innerHTML = '<option value="all">All teams</option>' + teams.map(function (t) {
      return '<option value="' + t.id + '">' + ui.esc(t.name) + '</option>';
    }).join('');
    teamSel.addEventListener('change', load);
    load();
  });

  function load() {
    api.getInsights(teamSel.value).then(render).catch(function (err) { ui.showError(root, err); });
  }

  function render(d) {
    root.innerHTML =
      section('allocation', 'Task allocation', allocationLead(d.allocation)) +
      section('progress', 'Project progress', progressLead(d.progress)) +
      section('resourcing', 'Resourcing', resourcingLead(d.resourcing)) +
      section('training', 'Training needs', trainingLead(d.training));

    drawAllocation(d.allocation);
    drawProgress(d.progress);
    drawResourcing(d.resourcing);
    drawTraining(d.training);
  }

  function section(id, title, lead) {
    return '<section class="panel" aria-labelledby="h-' + id + '"><h2 id="h-' + id + '">' + title + '</h2>' +
      '<p class="finding">' + lead + '</p><div id="c-' + id + '"></div></section>';
  }

  // ---------- 1. Allocation ----------
  function allocationLead(a) {
    if (a.suppressed) return 'Hidden: fewer than ' + cfg.MIN_GROUP + ' people in this group.';
    var even = a.halfHeldByPct >= 40;
    return (even ? 'Work is spread fairly evenly. ' : 'Work is concentrated. ') +
      'Half of the ' + a.totalOpen + ' open tasks sit with ' + a.halfHeldByPct + '% of the ' + a.headcount +
      ' people, an average of ' + a.average + ' each.';
  }
  function drawAllocation(a) {
    var el = document.getElementById('c-allocation');
    if (a.suppressed) { el.innerHTML = suppressedNote(); return; }
    charts.columns(el, a.buckets.map(function (b) {
      return { label: b.label, value: b.people,
        tip: '<strong>' + b.people + (b.people === 1 ? ' person' : ' people') + '</strong><br>with ' + b.label + ' open tasks' };
    }), {
      label: 'Number of people by how many open tasks they hold',
      xTitle: 'Open tasks per person (bars show number of people)',
      table: { headers: ['Open tasks', 'People'], rows: a.buckets.map(function (b) { return [b.label, b.people]; }) }
    });
  }

  // ---------- 2. Progress ----------
  function progressLead(ps) {
    var behind = ps.filter(function (p) { return p.status === 'behind' || p.status === 'at_risk'; });
    if (!ps.length) return 'No projects in this group.';
    if (!behind.length) return 'All ' + ps.length + ' projects are on track against their plan.';
    return behind.length + ' of ' + ps.length + ' projects are behind plan: ' +
      ui.listText(behind.map(function (p) { return ui.esc(p.name); })) + '.';
  }
  function drawProgress(ps) {
    charts.hbars(document.getElementById('c-progress'), ps.map(function (p) {
      return {
        label: p.name, value: p.progress.actual, display: p.progress.actual + '%',
        extra: ui.statusPill(p.status),
        tip: '<strong>' + ui.esc(p.name) + '</strong><br>' + p.progress.actual + '% done, plan ' +
          p.progress.expected + '%<br>' + p.totals.overdue + ' overdue, ' + ui.esc(ui.daysLeftText(p.daysLeft).toLowerCase())
      };
    }), {
      max: 100,
      table: { headers: ['Project', 'Done', 'Planned by today', 'Status'],
        rows: ps.map(function (p) { return [p.name, p.progress.actual + '%', p.progress.expected + '%', ui.STATUS[p.status].label]; }) }
    });
  }

  // ---------- 3. Resourcing ----------
  function resourcingLead(rs) {
    var short = rs.filter(function (r) { return r.level === 'critical'; });
    if (!short.length) return 'Every project has enough people-time left to clear its open work.';
    return short.length + (short.length === 1 ? ' project has' : ' projects have') +
      ' more open work than the team can finish before the deadline.';
  }
  function drawResourcing(rs) {
    var labels = { good: 'Enough', warning: 'Tight', critical: 'Short' };
    var shown = rs.map(function (r) {
      var pct = r.ratio === null ? 200 : Math.round(r.ratio * 100);
      return {
        label: r.name, value: Math.min(pct, 200),
        display: r.ratio === null ? 'Past deadline' : pct + '%',
        extra: ui.levelPill(r.level, labels[r.level]),
        tip: '<strong>' + ui.esc(r.name) + '</strong><br>' + r.demandDays + ' task-days open<br>' +
          r.capacityDays + ' people-days available<br>' + r.workingDaysLeft + ' working days left, ' + r.blocked + ' blocked'
      };
    });
    charts.hbars(document.getElementById('c-resourcing'), shown, {
      max: 200,
      ref: { value: 100, label: 'Line = 100%: open work exactly fills the time left. Above it, the team is short.' },
      table: { headers: ['Project', 'Open task-days', 'People-days left', 'Load', 'Blocked'],
        rows: rs.map(function (r) { return [r.name, r.demandDays, r.capacityDays, r.ratio === null ? 'Past deadline' : Math.round(r.ratio * 100) + '%', r.blocked]; }) }
    });
    var note = document.createElement('p');
    note.className = 'muted small';
    note.textContent = 'Assumes each member spends ' + Math.round(cfg.ASSUMED_ALLOCATION * 100) +
      '% of their time on one project. To be confirmed with the client.';
    document.getElementById('c-resourcing').appendChild(note);
  }

  // ---------- 4. Training ----------
  function trainingLead(ts) {
    var flagged = ts.filter(function (t) { return t.level === 'critical'; });
    if (!flagged.length) return 'No skill area stands out as needing training right now.';
    return 'Training suggested for ' + ui.listText(flagged.map(function (t) { return ui.esc(t.area); })) +
      ': more than ' + Math.round(cfg.TRAINING_FLAG * 100) + '% of tasks there finished late, were reopened or are overdue.';
  }
  function drawTraining(ts) {
    var labels = { good: 'No action', warning: 'Keep an eye on', critical: 'Training suggested' };
    var visible = ts.filter(function (t) { return !t.suppressed; });
    var hidden = ts.filter(function (t) { return t.suppressed; });
    var el = document.getElementById('c-training');
    charts.hbars(el, visible.map(function (t) {
      return {
        label: t.area, value: t.issueRate, display: t.issueRate + '%',
        extra: ui.levelPill(t.level, labels[t.level]),
        tip: '<strong>' + ui.esc(t.area) + '</strong><br>' + t.tasks + ' tasks, ' + t.people + ' people<br>' +
          t.late + ' finished late, ' + t.reopened + ' reopened, ' + t.overdue + ' overdue now'
      };
    }), {
      max: 100,
      ref: { value: cfg.TRAINING_FLAG * 100, label: 'Line = ' + Math.round(cfg.TRAINING_FLAG * 100) + '%, the point where training is suggested.' },
      table: { headers: ['Skill area', 'Tasks', 'Finished late', 'Reopened', 'Overdue', 'Issue rate'],
        rows: visible.map(function (t) { return [t.area, t.tasks, t.late, t.reopened, t.overdue, t.issueRate + '%']; }) }
    });
    if (hidden.length) {
      var p = document.createElement('p');
      p.className = 'muted small';
      p.textContent = 'Not shown: ' + hidden.map(function (t) { return t.area; }).join(', ') +
        '. Fewer than ' + cfg.MIN_GROUP + ' people worked on it, so the figure could identify someone.';
      el.appendChild(p);
    }
  }

  function suppressedNote() {
    return '<p class="empty">This figure is hidden because the group has fewer than ' + cfg.MIN_GROUP +
      ' people, and showing it could identify individuals.</p>';
  }
})(MIA.api, MIA.ui, MIA.charts, MIA.session, MIA.config);
