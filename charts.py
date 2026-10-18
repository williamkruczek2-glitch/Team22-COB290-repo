"""
charts.py - dependency-free charts (drawn with QPainter, nothing extra to install).   [was js/charts.js]
Every chart has hover tooltips and a "Show as table" view so nothing
depends on colour or a mouse.
"""
import math

from PySide6.QtCore import Qt, QRectF, QPointF, QSize, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QToolTip,
                               QSizePolicy)

import ui
from styles import T


def tableView(headers, rows):
    """'Show as table' toggle (the <details> element in the web version)."""
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 8, 0, 0)
    lay.setSpacing(6)
    summary = QPushButton('▸  Show as table')
    summary.setProperty('class', 'link')
    summary.setCursor(Qt.PointingHandCursor)
    table = makeTable(headers, rows)
    table.hide()

    def toggle():
        table.setVisible(not table.isVisible())
        summary.setText(('▾' if table.isVisible() else '▸') + '  Show as table')

    summary.clicked.connect(toggle)
    lay.addWidget(summary, alignment=Qt.AlignLeft)
    lay.addWidget(table)
    return box


def makeTable(headers, rows, bold=None):
    """A read-only table. bold: optional set of (row, col) cells to show in bold."""
    table = _Table(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.NoSelection)
    table.setFocusPolicy(Qt.NoFocus)
    table.setShowGrid(False)
    table.setTextElideMode(Qt.ElideNone)
    table.setWordWrap(True)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    for r, values in enumerate(rows):
        for c, value in enumerate(values):
            table.setItem(r, c, QTableWidgetItem(str(value)))
    for (r, c) in (bold or ()):
        f = table.item(r, c).font(); f.setBold(True); table.item(r, c).setFont(f)
    header = table.horizontalHeader()
    header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header.setSectionResizeMode(QHeaderView.ResizeToContents)
    header.setSectionResizeMode(0, QHeaderView.Stretch)
    table.fit()
    return table


class _Table(QTableWidget):
    """Table that grows to fit its rows, re-measuring when its width changes."""

    def fit(self):
        self.resizeRowsToContents()
        for i in range(self.rowCount()):
            self.setRowHeight(i, self.rowHeight(i) + 10)      # breathing room, like the web table padding
        self.setFixedHeight(self.horizontalHeader().sizeHint().height() +
                            sum(self.rowHeight(i) for i in range(self.rowCount())) + 2)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        QTimer.singleShot(0, self.fit)      # after the columns have settled


def _tip(widget, html):
    widget.setToolTip(html)


class _Track(QWidget):
    """One horizontal bar (hbar__track) with an optional reference line."""

    def __init__(self, pct, refPct):
        super().__init__()
        self.pct, self.refPct = pct, refPct
        self.setFixedHeight(22)
        self.setMinimumWidth(80)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        top, h = 4, 14
        w = max(2, self.pct / 100 * self.width())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(T['series-1']))
        p.drawRoundedRect(QRectF(0, top, w, h), 4, 4)
        p.drawRect(QRectF(0, top, min(w, 4), h))           # square left end, like the web version
        if self.refPct is not None:
            x = self.refPct / 100 * self.width()
            p.setPen(QPen(QColor(T['ink']), 2))
            p.drawLine(QPointF(x, 0), QPointF(x, top + h + 4))
        p.end()


class _RefKey(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(4, 14)

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(1, 0, 2, 14, QColor(T['ink']))
        p.end()


def hbars(el, rows, opts=None):
    """
    Horizontal bars.
    rows: [{ label, value, display, tip, extra }]   (extra = a widget, e.g. a pill)
    opts: { max, ref: { value, label }, table: { headers, rows } }
    """
    opts = opts or {}
    mx = opts.get('max') or max([r['value'] for r in rows] + [1])
    refPct = min(100, (opts['ref']['value'] / mx) * 100) if opts.get('ref') else None

    box = QWidget()
    grid = QGridLayout(box)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(4)
    grid.setColumnMinimumWidth(0, 200)
    grid.setColumnStretch(1, 1)
    grid.setColumnMinimumWidth(2, 64)
    grid.setColumnMinimumWidth(3, 172)
    for i, r in enumerate(rows):
        w = max(0, min(100, (r['value'] / mx) * 100))
        name = QLabel(r['label'])
        track = _Track(w, refPct)
        value = QLabel(f"<b>{ui.esc(r['display'])}</b>")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        for x in (name, track, value):
            _tip(x, r['tip'])
        grid.addWidget(name, i, 0)
        grid.addWidget(track, i, 1)
        grid.addWidget(value, i, 2)
        if r.get('extra'):
            _tip(r['extra'], r['tip'])
            grid.addWidget(r['extra'], i, 3, alignment=Qt.AlignLeft)
    el.addWidget(box)

    if opts.get('ref'):
        note = QHBoxLayout()
        note.setSpacing(8)
        note.addWidget(_RefKey())
        note.addWidget(ui.label(opts['ref']['label'], 'small'), 1)
        el.addLayout(note)
    if opts.get('table'):
        el.addWidget(tableView(opts['table']['headers'], opts['table']['rows']))


class _Columns(QWidget):
    def __init__(self, rows, accessibleName):
        super().__init__()
        self.rows = rows
        self.setAccessibleName(accessibleName)
        self.setFixedHeight(190)
        self.setMouseTracking(True)
        self.hits = []

    def sizeHint(self):
        return QSize(len(self.rows) * 128, 190)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        mx = max([r['value'] for r in self.rows] + [1])
        colW, gap = 110, 18
        valueH, labelH = 22, 26
        base = self.height() - labelH
        barArea = base - valueH
        bold = QFont(self.font()); bold.setBold(True)
        self.hits = []
        for i, r in enumerate(self.rows):
            x = i * (colW + gap)
            h = max(2, r['value'] / mx * barArea)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(T['series-1']))
            p.drawRoundedRect(QRectF(x + 4, base - h, colW - 8, h), 4, 4)
            p.drawRect(QRectF(x + 4, base - min(h, 4), colW - 8, min(h, 4)))
            p.setPen(QColor(T['ink']))
            p.setFont(bold)
            p.drawText(QRectF(x, base - h - valueH, colW, valueH), Qt.AlignCenter, str(r['value']))
            p.setFont(self.font())
            p.drawText(QRectF(x, base + 6, colW, labelH - 6), Qt.AlignHCenter | Qt.AlignTop, r['label'])
            self.hits.append((QRectF(x, 0, colW, self.height()), r['tip']))
        p.setPen(QPen(QColor(T['rule']), 1))
        p.drawLine(QPointF(0, base), QPointF(len(self.rows) * (colW + gap) - gap, base))
        p.end()

    def mouseMoveEvent(self, e):
        for rect, tip in self.hits:
            if rect.contains(e.position()):
                QToolTip.showText(e.globalPosition().toPoint(), tip, self)
                return
        QToolTip.hideText()


def columns(el, rows, opts):
    """Vertical columns (used for the workload histogram). rows: [{ label, value, tip }]"""
    el.addWidget(_Columns(rows, opts['label']), alignment=Qt.AlignLeft)
    el.addWidget(ui.label(opts['xTitle'], 'small'))
    if opts.get('table'):
        el.addWidget(tableView(opts['table']['headers'], opts['table']['rows']))


class _LegendKey(QWidget):
    def __init__(self, dashed):
        super().__init__()
        self.dashed = dashed
        self.setFixedSize(16, 12)

    def paintEvent(self, _):
        p = QPainter(self)
        pen = QPen(QColor(T['muted'] if self.dashed else T['series-1']), 2 if self.dashed else 3)
        if self.dashed:
            pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.drawLine(0, 6, 16, 6)
        p.end()


class _Burnup(QWidget):
    def __init__(self, points, total):
        super().__init__()
        self.points, self.total = points, max(1, total)
        self.setFixedHeight(240)
        self.setMouseTracking(True)
        self.hover = None
        last = points[-1]
        self.setAccessibleName(f"Burn-up: {last['actual']} of {total} tasks completed against "
                               f"{last['planned']} planned by today")
        self.m = {'t': 16, 'r': 16, 'b': 28, 'l': 36}

    def x(self, i):
        iw = self.width() - self.m['l'] - self.m['r']
        n = len(self.points)
        return self.m['l'] + (iw / 2 if n == 1 else (i / (n - 1)) * iw)

    def y(self, v):
        ih = self.height() - self.m['t'] - self.m['b']
        return self.m['t'] + ih - (v / self.total) * ih

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m, W, H, n = self.m, self.width(), self.height(), len(self.points)
        iw = W - m['l'] - m['r']
        tick = QFont(self.font()); tick.setPointSizeF(8.5)
        p.setFont(tick)

        stepY = next((k for k in [1, 2, 5, 10, 20, 25, 50] if self.total / k <= 5), 100)
        for v in range(0, self.total + 1, stepY):
            p.setPen(QPen(QColor(T['rule']), 1))
            p.drawLine(QPointF(m['l'], self.y(v)), QPointF(W - m['r'], self.y(v)))
            p.setPen(QColor(T['muted']))
            p.drawText(QRectF(0, self.y(v) - 8, m['l'] - 8, 16), Qt.AlignRight | Qt.AlignVCenter, str(v))

        step = math.ceil(n / max(2, math.floor(iw / 70)))
        for i, pt in enumerate(self.points):
            if i % step and i != n - 1:
                continue
            p.drawText(QRectF(self.x(i) - 40, H - 20, 80, 16), Qt.AlignCenter, ui.fmtDate(pt['date']))

        for key, colour, dashed in (('planned', T['muted'], True), ('actual', T['series-1'], False)):
            pen = QPen(QColor(colour), 2)
            pen.setJoinStyle(Qt.RoundJoin)
            if dashed:
                pen.setDashPattern([2.5, 2])
            p.setPen(pen)
            for i in range(1, n):
                p.drawLine(QPointF(self.x(i - 1), self.y(self.points[i - 1][key])),
                           QPointF(self.x(i), self.y(self.points[i][key])))

        last = self.points[-1]
        p.setPen(QPen(QColor(T['surface']), 2))
        p.setBrush(QColor(T['series-1']))
        p.drawEllipse(QPointF(self.x(n - 1), self.y(last['actual'])), 4, 4)
        bold = QFont(tick); bold.setBold(True)
        p.setFont(bold)
        p.setPen(QColor(T['ink']))
        p.drawText(QRectF(self.x(n - 1) - 8 - 120, self.y(last['actual']) + 6, 120, 16),
                   Qt.AlignRight | Qt.AlignVCenter, f"{last['actual']} done")

        if self.hover is not None:
            p.setPen(QPen(QColor(T['ink-2']), 1))
            p.drawLine(QPointF(self.x(self.hover), m['t']), QPointF(self.x(self.hover), m['t'] + H - m['t'] - m['b']))
        p.end()

    def mouseMoveEvent(self, e):
        n = len(self.points)
        iw = self.width() - self.m['l'] - self.m['r']
        i = round(((e.position().x() - self.m['l']) / iw) * (n - 1)) if n > 1 else 0
        i = max(0, min(n - 1, i))
        self.hover = i
        self.update()
        pt = self.points[i]
        note = ('On or ahead of plan' if pt['actual'] - pt['planned'] >= 0
                else f"{pt['planned'] - pt['actual']} behind plan")
        QToolTip.showText(e.globalPosition().toPoint(),
                          f"<strong>{ui.fmtDate(pt['date'])}</strong><br>Planned: {pt['planned']}"
                          f"<br>Completed: {pt['actual']}<br><span style='color:{T['muted']}'>{note}</span>", self)

    def leaveEvent(self, _):
        self.hover = None
        self.update()
        QToolTip.hideText()


def burnup(el, points, total):
    """Burn-up line chart: planned vs completed tasks over time."""
    legend = QHBoxLayout()
    legend.setSpacing(6)
    for dashed, words in ((True, 'Planned (tasks due)'), (False, 'Completed')):
        legend.addWidget(_LegendKey(dashed))
        legend.addWidget(ui.label(words, 'lede'))
        legend.addSpacing(12)
    legend.addStretch()
    el.addLayout(legend)
    el.addWidget(_Burnup(points, total))
    el.addWidget(tableView(['Week of', 'Planned', 'Completed'],
                           [[ui.fmtDate(p['date']), p['planned'], p['actual']] for p in points]))
