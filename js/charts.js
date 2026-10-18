/*
 * charts.js — dependency-free charts (no CDN needed when the markers open
 * the prototype offline). Every chart has hover tooltips, keyboard focus
 * and a "Show as table" view so nothing depends on colour or a mouse.
 */
var MIA = window.MIA || {};

MIA.charts = (function (ui) {
  var esc = ui.esc;

  function tableView(headers, rows) {
    return '<details class="tableview"><summary>Show as table</summary><table><thead><tr>' +
      headers.map(function (h) { return '<th scope="col">' + esc(h) + '</th>'; }).join('') +
      '</tr></thead><tbody>' +
      rows.map(function (r) { return '<tr>' + r.map(function (c) { return '<td>' + esc(c) + '</td>'; }).join('') + '</tr>'; }).join('') +
      '</tbody></table></details>';
  }

  function bindTips(root) {
    root.querySelectorAll('[data-tip]').forEach(function (n) {
      n.addEventListener('mousemove', function (e) { ui.tooltip(n.getAttribute('data-tip'), e); });
      n.addEventListener('mouseleave', function () { ui.tooltip(null); });
      n.addEventListener('focus', function () {
        var r = n.getBoundingClientRect();
        ui.tooltip(n.getAttribute('data-tip'), { clientX: r.left + r.width / 2, clientY: r.bottom });
      });
      n.addEventListener('blur', function () { ui.tooltip(null); });
    });
  }

  /*
   * Horizontal bars.
   * rows: [{ label, value, display, tip, extra }]
   * opts: { max, ref: { value, label }, table: { headers, rows } }
   */
  function hbars(el, rows, opts) {
    opts = opts || {};
    var max = opts.max || Math.max.apply(null, rows.map(function (r) { return r.value; }).concat([1]));
    var refPct = opts.ref ? Math.min(100, (opts.ref.value / max) * 100) : null;
    var html = '<div class="hbars">' + rows.map(function (r) {
      var w = Math.max(0, Math.min(100, (r.value / max) * 100));
      return '<div class="hbar" tabindex="0" data-tip="' + esc(r.tip) + '">' +
        '<span class="hbar__label">' + esc(r.label) + '</span>' +
        '<span class="hbar__track">' +
          '<span class="hbar__fill" style="width:' + w + '%"></span>' +
          (refPct !== null ? '<span class="hbar__ref" style="left:' + refPct + '%"></span>' : '') +
        '</span>' +
        '<span class="hbar__value">' + esc(r.display) + '</span>' +
        (r.extra ? '<span class="hbar__extra">' + r.extra + '</span>' : '') +
      '</div>';
    }).join('') + '</div>';
    if (opts.ref) {
      html += '<p class="chart-note"><span class="ref-key" aria-hidden="true"></span>' + esc(opts.ref.label) + '</p>';
    }
    if (opts.table) html += tableView(opts.table.headers, opts.table.rows);
    el.innerHTML = html;
    bindTips(el);
  }

  /* Vertical columns (used for the workload histogram). */
  function columns(el, rows, opts) {
    var max = Math.max.apply(null, rows.map(function (r) { return r.value; }).concat([1]));
    var html = '<div class="cols" role="img" aria-label="' + esc(opts.label) + '">' + rows.map(function (r) {
      var h = (r.value / max) * 100;
      return '<div class="col" tabindex="0" data-tip="' + esc(r.tip) + '">' +
        '<span class="col__value">' + esc(r.value) + '</span>' +
        '<span class="col__bar"><span class="col__fill" style="height:' + h + '%"></span></span>' +
        '<span class="col__label">' + esc(r.label) + '</span></div>';
    }).join('') + '</div>';
    html += '<p class="chart-axis">' + esc(opts.xTitle) + '</p>';
    if (opts.table) html += tableView(opts.table.headers, opts.table.rows);
    el.innerHTML = html;
    bindTips(el);
  }

  /*
   * Burn-up line chart: planned vs completed tasks over time.
   * points: [{ date, planned, actual }], total: number of tasks
   */
  function burnup(el, points, total) {
    function draw() {
      var W = Math.max(300, el.clientWidth), H = 240;
      var m = { t: 16, r: 16, b: 28, l: 36 };
      var iw = W - m.l - m.r, ih = H - m.t - m.b;
      var n = points.length;
      var x = function (i) { return m.l + (n === 1 ? iw / 2 : (i / (n - 1)) * iw); };
      var y = function (v) { return m.t + ih - (v / total) * ih; };
      var path = function (key) {
        return points.map(function (p, i) { return (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(p[key]).toFixed(1); }).join(' ');
      };
      var stepY = [1, 2, 5, 10, 20, 25, 50].filter(function (k) { return total / k <= 5; })[0] || 100;
      var ticks = []; for (var v0 = 0; v0 <= total; v0 += stepY) ticks.push(v0);
      var grid = ticks.map(function (v) {
        return '<line class="grid" x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '"/>' +
          '<text class="tick" x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" text-anchor="end">' + v + '</text>';
      }).join('');
      var step = Math.ceil(n / Math.max(2, Math.floor(iw / 70)));
      var xt = points.map(function (p, i) {
        if (i % step && i !== n - 1) return '';
        return '<text class="tick" x="' + x(i) + '" y="' + (H - 8) + '" text-anchor="middle">' + ui.fmtDate(p.date) + '</text>';
      }).join('');
      var last = points[n - 1];
      el.innerHTML =
        '<div class="legend"><span><i class="key key--plan"></i>Planned (tasks due)</span>' +
        '<span><i class="key key--actual"></i>Completed</span></div>' +
        '<svg width="' + W + '" height="' + H + '" role="img" aria-label="Burn-up: ' + last.actual +
          ' of ' + total + ' tasks completed against ' + last.planned + ' planned by today">' +
          grid + xt +
          '<path class="line line--plan" d="' + path('planned') + '"/>' +
          '<path class="line line--actual" d="' + path('actual') + '"/>' +
          '<circle class="dot" cx="' + x(n - 1) + '" cy="' + y(last.actual) + '" r="4"/>' +
          '<text class="direct-label" x="' + (x(n - 1) - 8) + '" y="' + (y(last.actual) + 18) + '" text-anchor="end">' +
            last.actual + ' done</text>' +
          '<line class="crosshair" y1="' + m.t + '" y2="' + (m.t + ih) + '" style="display:none"/>' +
          '<rect class="hit" x="' + m.l + '" y="' + m.t + '" width="' + iw + '" height="' + ih + '"/>' +
        '</svg>' +
        tableView(['Week of', 'Planned', 'Completed'], points.map(function (p) { return [ui.fmtDate(p.date), p.planned, p.actual]; }));

      var svg = el.querySelector('svg'), hair = el.querySelector('.crosshair');
      el.querySelector('.hit').addEventListener('mousemove', function (e) {
        var bx = e.clientX - svg.getBoundingClientRect().left;
        var i = Math.round(((bx - m.l) / iw) * (n - 1));
        i = Math.max(0, Math.min(n - 1, i));
        var p = points[i];
        hair.setAttribute('x1', x(i)); hair.setAttribute('x2', x(i)); hair.style.display = '';
        ui.tooltip('<strong>' + ui.fmtDate(p.date) + '</strong><br>Planned: ' + p.planned +
          '<br>Completed: ' + p.actual + '<br><span class="muted">' + (p.actual - p.planned >= 0 ? 'On or ahead of plan' :
          (p.planned - p.actual) + ' behind plan') + '</span>', e);
      });
      el.querySelector('.hit').addEventListener('mouseleave', function () { hair.style.display = 'none'; ui.tooltip(null); });
    }
    draw();
    var t; window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(draw, 120); });
  }

  return { hbars: hbars, columns: columns, burnup: burnup, tableView: tableView };
})(MIA.ui);

window.MIA = MIA;
