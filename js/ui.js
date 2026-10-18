/*
 * ui.js — small shared helpers: escaping, dates, status labels, nav, tooltip.
 * Teammates can reuse these when the pages are merged.
 */



var MIA = window.MIA || {};

MIA.ui = (function () {
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function fmtDate(isoStr) {
    return new Date(isoStr).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  }

  function daysLeftText(n) {
    if (n < 0) return Math.abs(n) + (n === -1 ? ' day' : ' days') + ' past deadline';
    if (n === 0) return 'Due today';
    return n + (n === 1 ? ' day' : ' days') + ' left';
  }

  // Status never relies on colour alone: icon + word + colour.
  var STATUS = {
    on_track: { label: 'On track', tone: 'good', icon: '✓' },
    behind:   { label: 'Behind plan', tone: 'warning', icon: '!' },
    at_risk:  { label: 'At risk', tone: 'critical', icon: '▲' },
    complete: { label: 'Complete', tone: 'good', icon: '✓' }
  };
  var LEVEL = {
    good:     { tone: 'good', icon: '✓' },
    warning:  { tone: 'warning', icon: '!' },
    critical: { tone: 'critical', icon: '▲' }
  };
  var TASK_STATUS = { todo: 'To do', in_progress: 'In progress', blocked: 'Blocked', done: 'Done' };

  function pill(tone, icon, label) {
    return '<span class="pill pill--' + tone + '"><span class="pill__icon" aria-hidden="true">' +
      icon + '</span>' + esc(label) + '</span>';
  }
  function statusPill(status) { var s = STATUS[status]; return pill(s.tone, s.icon, s.label); }
  function levelPill(level, label) { var l = LEVEL[level]; return pill(l.tone, l.icon, label); }

  // Left-hand navigation. Links to teammates' pages are placeholders until merge weekend.
  function renderNav(active) {
    var user = MIA.session.get();
    var items = [
      { key: 'todo', label: 'My to-do list', href: '#', owner: 'R01' },
      { key: 'dashboard', label: 'Project dashboard', href: 'dashboard.html', managerOnly: true },
      { key: 'workload', label: 'Team workload', href: '#', owner: 'R03' },
      { key: 'knowledge', label: 'Knowledge base', href: '#', owner: 'R04/R05' },
      { key: 'insights', label: 'Insights', href: 'insights.html', managerOnly: true }
    ];
    var links = items.filter(function (i) { return !i.managerOnly || user.role === 'manager'; })
      .map(function (i) {
        var cur = i.key === active ? ' aria-current="page"' : '';
        var ph = i.owner ? ' data-placeholder="' + i.owner + '" title="Merged in from ' + i.owner + '"' : '';
        return '<li><a href="' + i.href + '"' + cur + ph + '>' + esc(i.label) + '</a></li>';
      }).join('');
    var initials = user.name.split(' ').map(function (p) { return p[0]; }).join('');
    document.getElementById('nav').innerHTML =
      '<a class="brand" href="dashboard.html"><span class="brand__mark" aria-hidden="true">M</span>Make-It-All</a>' +
      '<ul class="nav__list">' + links + '</ul>' +
      '<div class="nav__user"><span class="avatar" aria-hidden="true">' + esc(initials) + '</span>' +
      '<span><strong>' + esc(user.name) + '</strong><br><span class="muted">' +
      (user.role === 'manager' ? 'Project manager' : 'Staff') + '</span></span></div>';
  }

  // One shared tooltip for every chart.
  var tip;
  function tooltip(html, evt) {
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'tooltip'; tip.setAttribute('role', 'status');
      document.body.appendChild(tip);
    }
    if (html === null) { tip.hidden = true; return; }
    tip.innerHTML = html; tip.hidden = false;
    var x = evt.clientX + 14, y = evt.clientY + 14;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    if (x + w > window.innerWidth - 8) x = evt.clientX - w - 14;
    if (y + h > window.innerHeight - 8) y = evt.clientY - h - 14;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }

  function showError(el, err) {
    el.innerHTML = '<p class="notice notice--error">Couldn’t load this view: ' + esc(err.message) +
      '. Reload the page to try again.</p>';
  }

  // ['a','b','c'] -> "a, b and c"
  function listText(items) {
    return items.length < 2 ? items.join('') : items.slice(0, -1).join(', ') + ' and ' + items[items.length - 1];
  }

  return { listText: listText, esc: esc, fmtDate: fmtDate, daysLeftText: daysLeftText, statusPill: statusPill,
    levelPill: levelPill, STATUS: STATUS, TASK_STATUS: TASK_STATUS, renderNav: renderNav,
    tooltip: tooltip, showError: showError };
})();

window.MIA = MIA;
