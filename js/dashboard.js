/*
 * dashboard.js — R02: manager's dashboard.
 * Shows every project the signed-in manager is responsible for, how far
 * along it is against plan, and what needs attention.
 */
(function (api, ui, session) {
  ui.renderNav('dashboard');
  var user = session.get();
  var listEl = document.getElementById('project-list');
  var summaryEl = document.getElementById('summary');
  var all = [];

  document.getElementById('greeting').textContent = 'Projects you manage, ' + user.name.split(' ')[0];

  if (!session.isManager()) {
    listEl.innerHTML = '<p class="notice">The project dashboard is for managers and team leaders. ' +
      'Your own tasks are in <a href="#">My to-do list</a>.</p>';
    return;
  }

  api.getManagerProjects(user.id).then(function (projects) {
    all = projects;
    renderSummary(projects);
    render();
  }).catch(function (err) { ui.showError(listEl, err); });

  document.getElementById('filter').addEventListener('change', render);
  document.getElementById('sort').addEventListener('change', render);

  function renderSummary(ps) {
    var sum = function (f) { return ps.reduce(function (s, p) { return s + f(p); }, 0); };
    var needs = ps.filter(function (p) { return p.status === 'at_risk' || p.status === 'behind'; }).length;
    var stats = [
      { n: ps.length, label: 'Active projects' },
      { n: needs, label: needs === 1 ? 'Project needs attention' : 'Projects need attention', tone: needs ? 'critical' : '' },
      { n: sum(function (p) { return p.totals.overdue; }), label: 'Overdue tasks' },
      { n: sum(function (p) { return p.totals.blocked; }), label: 'Blocked tasks' }
    ];
    summaryEl.innerHTML = stats.map(function (s) {
      return '<div class="stat' + (s.tone ? ' stat--' + s.tone : '') + '"><span class="stat__n">' + s.n +
        '</span><span class="stat__label">' + ui.esc(s.label) + '</span></div>';
    }).join('');
  }

  function render() {
    var filter = document.getElementById('filter').value;
    var sort = document.getElementById('sort').value;
    var ps = all.filter(function (p) {
      return filter === 'all' || (filter === 'attention' && (p.status === 'at_risk' || p.status === 'behind'));
    });
    var order = { at_risk: 0, behind: 1, on_track: 2, complete: 3 };
    ps.sort(function (a, b) {
      if (sort === 'deadline') return a.daysLeft - b.daysLeft;
      if (sort === 'progress') return a.progress.gap - b.progress.gap;
      return order[a.status] - order[b.status] || a.daysLeft - b.daysLeft;
    });

    if (!ps.length) {
      listEl.innerHTML = '<p class="notice">No projects need attention right now. ' +
        'Choose “All projects” to see everything you manage.</p>';
      return;
    }
    listEl.innerHTML = ps.map(row).join('');
  }

  function row(p) {
    var g = p.progress.gap;
    var gapText = g >= 0 ? (g === 0 ? 'Exactly on plan' : g + ' pts ahead of plan')
                         : Math.abs(g) + ' pts behind plan';
    return '<article class="project">' +
      '<div class="project__head">' +
        '<h3><a href="project.html?id=' + encodeURIComponent(p.id) + '">' + ui.esc(p.name) + '</a></h3>' +
        ui.statusPill(p.status) +
      '</div>' +
      '<p class="project__meta">' + ui.esc(p.team) + ' team, ' + p.memberCount + ' people. Deadline ' +
        ui.fmtDate(p.endDate) + ' (' + ui.daysLeftText(p.daysLeft) + ')</p>' +
      '<div class="progress" role="img" aria-label="' + p.progress.actual + '% of tasks done; plan says ' +
        p.progress.expected + '% by today">' +
        '<div class="progress__fill" style="width:' + p.progress.actual + '%"></div>' +
        '<div class="progress__plan" style="left:' + p.progress.expected + '%"><span>Plan</span></div>' +
      '</div>' +
      '<div class="project__foot">' +
        '<span><strong>' + p.progress.actual + '%</strong> done, ' + gapText + '</span>' +
        '<span class="counts">' +
          count(p.totals.open, 'open') + count(p.totals.overdue, 'overdue', p.totals.overdue > 0) +
          count(p.totals.blocked, 'blocked', p.totals.blocked > 0) +
        '</span>' +
      '</div>' +
    '</article>';
  }

  function count(n, label, flag) {
    return '<span class="count' + (flag ? ' count--flag' : '') + '"><strong>' + n + '</strong> ' + label + '</span>';
  }
})(MIA.api, MIA.ui, MIA.session);
