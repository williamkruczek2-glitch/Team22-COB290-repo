/*
 * mockData.js — stand-in for the database (Part 1 has no DB).
 *
 * Every array here mirrors a future table:
 *   teams, employees, projects, tasks
 * In Part 2, delete this file and point api.js at the real endpoints.
 * Dates are generated relative to "today" so the demo always looks current.
 * A seeded random generator keeps the data identical on every page load.
 */
var MIA = window.MIA || {};

(function () {
  // Seeded PRNG (mulberry32) — same output every run.
  function rng(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  var rand = rng(290);
  var pick = function (arr) { return arr[Math.floor(rand() * arr.length)]; };

  var DAY = 86400000;
  var today = new Date(); today.setHours(0, 0, 0, 0);
  var d = function (offset) { return new Date(today.getTime() + offset * DAY); };
  var iso = function (date) { return date.toISOString().slice(0, 10); };

  // Skill areas line up with the Topics in the client letter (R04),
  // so training needs can later link to knowledge-base posts.
  var areas = ['Software Development', 'Software Issues', 'Printing',
               'Networking', 'Hardware', 'Admin & Procurement'];
  // Higher = more tasks finish late or get reopened (creates a training signal).
  var areaDifficulty = { 'Software Development': 0.12, 'Software Issues': 0.18,
    'Printing': 0.38, 'Networking': 0.34, 'Hardware': 0.14, 'Admin & Procurement': 0.08 };

  var teams = [
    { id: 'T1', name: 'Software Development' },
    { id: 'T2', name: 'Infrastructure' },
    { id: 'T3', name: 'Admin & Support' }
  ];

  var employees = [
    // Managers — the client's project-manager representatives
    { id: 'E01', name: 'Dilip Shah',     email: 'dilip.shah@make-it-all.co.uk',   teamId: 'T1', role: 'manager' },
    { id: 'E02', name: 'Emma Clarke',    email: 'emma.clarke@make-it-all.co.uk',  teamId: 'T2', role: 'manager' },
    // Software Development
    { id: 'E03', name: 'Clara Novak',    email: 'clara.novak@make-it-all.co.uk',  teamId: 'T1', role: 'specialist' },
    { id: 'E04', name: 'Bert Hughes',    email: 'bert.hughes@make-it-all.co.uk',  teamId: 'T1', role: 'specialist' },
    { id: 'E05', name: 'Priya Natarajan',email: 'priya.n@make-it-all.co.uk',      teamId: 'T1', role: 'specialist' },
    { id: 'E06', name: 'Tom Okafor',     email: 'tom.okafor@make-it-all.co.uk',   teamId: 'T1', role: 'specialist' },
    { id: 'E07', name: 'Hannah Reid',    email: 'hannah.reid@make-it-all.co.uk',  teamId: 'T1', role: 'specialist' },
    // Infrastructure
    { id: 'E08', name: 'Luis Moreno',    email: 'luis.moreno@make-it-all.co.uk',  teamId: 'T2', role: 'specialist' },
    { id: 'E09', name: 'Aisha Begum',    email: 'aisha.begum@make-it-all.co.uk',  teamId: 'T2', role: 'specialist' },
    { id: 'E10', name: 'Sam Whitaker',   email: 'sam.whitaker@make-it-all.co.uk', teamId: 'T2', role: 'specialist' },
    { id: 'E11', name: 'Grace Lin',      email: 'grace.lin@make-it-all.co.uk',    teamId: 'T2', role: 'specialist' },
    { id: 'E12', name: 'Owen Price',     email: 'owen.price@make-it-all.co.uk',   teamId: 'T2', role: 'specialist' },
    // Admin & Support
    { id: 'E13', name: 'Alice Morgan',   email: 'alice.morgan@make-it-all.co.uk', teamId: 'T3', role: 'manager' },
    { id: 'E14', name: 'Ruth Adeyemi',   email: 'ruth.adeyemi@make-it-all.co.uk', teamId: 'T3', role: 'staff' },
    { id: 'E15', name: 'Jack Dawson',    email: 'jack.dawson@make-it-all.co.uk',  teamId: 'T3', role: 'staff' },
    { id: 'E16', name: 'Mei Chen',       email: 'mei.chen@make-it-all.co.uk',     teamId: 'T3', role: 'staff' },
    { id: 'E17', name: 'Kofi Mensah',    email: 'kofi.mensah@make-it-all.co.uk',  teamId: 'T3', role: 'staff' }
  ];

  // health = share of due tasks actually done (drives on-track / behind / at-risk)
  var projectSeeds = [
    { id: 'P1', code: 'HTM', name: 'Helpdesk ticket migration', managerId: 'E01', teamId: 'T1',
      start: -60, end: 30, n: 34, health: 0.92, members: ['E03','E04','E05','E14','E15'],
      areas: ['Software Development','Software Issues','Admin & Procurement'],
      description: 'Move the old email-based helpdesk into the new ticketing workflow.' },
    { id: 'P2', code: 'PFR', name: 'Printer fleet refresh', managerId: 'E01', teamId: 'T2', start: -45, end: 8,
      n: 26, health: 0.55, members: ['E08','E09','E16'], areas: ['Printing','Hardware','Networking'],
      description: 'Replace 40 office printers and move them onto managed print queues.' },
    { id: 'P3', code: 'PPU', name: 'Payroll portal upgrade', managerId: 'E01', teamId: 'T1', start: -20, end: 70,
      n: 22, health: 0.80, members: ['E06','E07','E03','E17'], areas: ['Software Development','Software Issues'],
      description: 'Upgrade the payroll self-service portal and retire the legacy login.' },
    { id: 'P4', code: 'NSR', name: 'Network switch replacement', managerId: 'E02', teamId: 'T2', start: -80, end: 5,
      n: 30, health: 0.70, members: ['E10','E11','E12','E09'], areas: ['Networking','Hardware'],
      description: 'Swap end-of-life switches across both office floors.' },
    { id: 'P5', code: 'NSO', name: 'New starter onboarding pack', managerId: 'E13', teamId: 'T3', start: -30, end: 45,
      n: 18, health: 0.95, members: ['E14','E15','E16','E17'], areas: ['Admin & Procurement','Printing'],
      description: 'One checklist and kit for every new starter, from desk to accounts.' }
  ];

  var titles = {
    'Software Development': ['Build import script', 'Write API endpoint', 'Add form validation', 'Code review', 'Write unit tests', 'Refactor data model'],
    'Software Issues': ['Fix login timeout', 'Investigate slow query', 'Patch email parser', 'Resolve broken export', 'Triage bug backlog'],
    'Printing': ['Configure print queue', 'Install printer drivers', 'Set up secure release', 'Map floor printers', 'Test duplex defaults'],
    'Networking': ['Update VLAN config', 'Patch switch firmware', 'Run cable survey', 'Configure port security', 'Test failover link'],
    'Hardware': ['Order replacement units', 'Asset-tag new kit', 'Dispose of old units', 'Install rack hardware'],
    'Admin & Procurement': ['Raise purchase order', 'Update supplier list', 'Write user guide', 'Book training room', 'Collect sign-off']
  };

  var projects = [], tasks = [], taskNo = 1;

  projectSeeds.forEach(function (s) {
    projects.push({ id: s.id, code: s.code, name: s.name, managerId: s.managerId, teamId: s.teamId,
      startDate: iso(d(s.start)), endDate: iso(d(s.end)), memberIds: s.members, description: s.description });

    for (var i = 0; i < s.n; i++) {
      var area = pick(s.areas);
      var span = s.end - s.start;
      var dueOff = Math.round(s.start + 5 + rand() * (span - 5));
      var est = 1 + Math.floor(rand() * 5);             // estimate in working days
      var createdOff = Math.max(s.start, dueOff - est - Math.floor(rand() * 10));
      var isPastDue = dueOff <= 0;
      var doneChance = isPastDue ? s.health : s.health * 0.22;
      var done = rand() < doneChance;
      var difficulty = areaDifficulty[area];
      var status, completed = null;

      if (done) {
        status = 'done';
        var late = rand() < difficulty ? 1 + Math.floor(rand() * 6) : -Math.floor(rand() * 3);
        var compOff = Math.min(0, dueOff + late);
        completed = iso(d(Math.max(createdOff + 1, compOff)));
      } else {
        var r = rand();
        status = r < 0.18 ? 'blocked' : r < 0.6 ? 'in_progress' : 'todo';
        if (createdOff > 0) status = 'todo';
      }

      tasks.push({
        id: 'K' + String(taskNo++).padStart(3, '0'),
        projectId: s.id,
        title: pick(titles[area]),
        area: area,
        assigneeId: pick(s.members),
        status: status,                      // todo | in_progress | blocked | done
        priority: pick(['low', 'medium', 'medium', 'high']),
        estimateDays: est,
        createdDate: iso(d(createdOff)),
        dueDate: iso(d(dueOff)),
        completedDate: completed,
        reopened: rand() < difficulty * 0.6   // was marked done, then sent back
      });
    }
  });

  MIA.db = { teams: teams, employees: employees, projects: projects, tasks: tasks, areas: areas, today: iso(today) };
  window.MIA = MIA;
})();
