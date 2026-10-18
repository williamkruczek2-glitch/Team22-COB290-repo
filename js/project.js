/*
 * project.js — R02 drill-down: one project in detail.
 * Burn-up (planned vs completed), task status breakdown, overdue and
 * upcoming tasks. Reached from the dashboard via project.html?id=P1
 */
(function (api, ui, charts, session) {
  ui.renderNav('dashboard');
  var main = document.getElementById('detail');
  var id = new URLSearchParams(location.search).get('id') || 'P1';

  if (!session.isManager()) {
    main.innerHTML = '<p class="notice">Project details are for managers and team leaders.</p>';
    return;
  }

  api.getProjectDetail(id).then(render).catch(function (err) { ui.showError(main, err); });

  function render(p) {
    document.title = p.name + ' – Make-It-All';
    document.getElementById('crumb').textContent = p.name;

    var statusOrder = ['done', 'in_progress', 'blocked', 'todo'];
    var counts = {}; p.byStatus.forEach(function (s) { counts[s.status] = s.count; });
    var stack = statusOrder.map(function (s) {
      var w = (counts[s] / p.totals.total) * 100;
      return w ? '<span class="stack__seg stack__seg--' + s + '" style="width:' + w + '%" tabindex="0" data-tip="' +
        ui.esc('<strong>' + ui.TASK_STATUS[s] + '</strong><br>' + counts[s] + ' tasks (' + Math.round(w) + '%)') + '"></span>' : '';
    }).join('');
    var stackKey = statusOrder.map(function (s) {
      return '<span><i class="key key--' + s + '"></i>' + ui.TASK_STATUS[s] + ' <strong>' + counts[s] + '</strong></span>';
    }).join('');

    main.innerHTML =
      '<header class="page-head">' +
        '<div><h1>' + ui.esc(p.name) + '</h1><p class="lede">' + ui.esc(p.description) + '</p></div>' +
        ui.statusPill(p.status) +
      '</header>' +
      '<dl class="facts">' +
        fact('Done', p.progress.actual + '%') +
        fact('Planned by today', p.progress.expected + '%') +
        fact('Deadline', ui.fmtDate(p.endDate) + ', ' + ui.daysLeftText(p.daysLeft).toLowerCase()) +
        fact('Team', p.team + ', ' + p.memberCount + ' people') +
      '</dl>' +
      '<section class="panel"><h2>Progress against plan</h2>' +
        '<p class="panel__sub">Tasks completed each week compared with tasks scheduled to be due.</p>' +
        '<div id="burnup"></div></section>' +
      '<section class="panel"><h2>Where the ' + p.totals.total + ' tasks are</h2>' +
        '<div class="stack">' + stack + '</div><div class="legend">' + stackKey + '</div></section>' +
      '<div class="two-col">' +
        taskPanel('Overdue', p.overdueTasks, true, 'Nothing overdue on this project.') +
        taskPanel('Due in the next 14 days', p.upcomingTasks, false, 'No open tasks due in the next two weeks.') +
      '</div>' +
      '<p class="muted small">Named workload for each team member is on the Team workload page (R03).</p>';

    charts.burnup(document.getElementById('burnup'), p.burnup, p.totals.total);
    main.querySelectorAll('.stack [data-tip]').forEach(function (n) {
      n.addEventListener('mousemove', function (e) { ui.tooltip(n.getAttribute('data-tip'), e); });
      n.addEventListener('mouseleave', function () { ui.tooltip(null); });
    });
  }

  function fact(k, v) { return '<div><dt>' + ui.esc(k) + '</dt><dd>' + ui.esc(v) + '</dd></div>'; }

  function taskPanel(title, tasks, overdue, empty) {
    var body = tasks.length ? '<table class="tasks"><thead><tr><th scope="col">Task</th><th scope="col">Assigned to</th>' +
      '<th scope="col">' + (overdue ? 'Late by' : 'Due') + '</th><th scope="col">Status</th></tr></thead><tbody>' +
      tasks.map(function (t) {
        return '<tr><td>' + ui.esc(t.title) + '<br><span class="muted small">' + ui.esc(t.area) + '</span></td>' +
          '<td>' + ui.esc(t.assignee) + '</td>' +
          '<td>' + (overdue ? t.daysOverdue + (t.daysOverdue === 1 ? ' day' : ' days') : ui.fmtDate(t.dueDate)) + '</td>' +
          '<td><span class="tstatus tstatus--' + t.status + '">' + ui.TASK_STATUS[t.status] + '</span></td></tr>';
      }).join('') + '</tbody></table>' : '<p class="empty">' + empty + '</p>';
    return '<section class="panel"><h2>' + title + ' <span class="badge">' + tasks.length + '</span></h2>' + body + '</section>';
  }
})(MIA.api, MIA.ui, MIA.charts, MIA.session);
