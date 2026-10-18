"""
dashboard.py - R02: manager's dashboard.   [was js/dashboard.js + dashboard.html]
Shows every project the signed-in manager is responsible for, how far
along it is against plan, and what needs attention.
"""
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QLabel

import api
import session
import ui
from styles import T


class DashboardPage(ui.Page):
    def __init__(self):
        super().__init__()
        user = session.get()
        self.all = []

        # --- page header (dashboard.html) ---
        self.greeting = ui.label('Projects you manage', 'h1')
        self.main.addWidget(self.greeting)
        self.main.addWidget(ui.label("Progress against plan for each project you're responsible for. "
                                     "The black line on each bar shows where the plan says you should be today.", 'lede'))
        self.summaryEl = QFrame()
        self.summaryEl.setObjectName('summary')
        self.summaryLay = QHBoxLayout(self.summaryEl)
        self.summaryLay.setContentsMargins(0, 0, 0, 0)
        self.summaryLay.setSpacing(1)
        self.main.addWidget(self.summaryEl)

        self.filter = QComboBox()
        self.filter.addItem('All projects', 'all')
        self.filter.addItem('Needs attention', 'attention')
        self.sort = QComboBox()
        self.sort.addItem('Most at risk first', 'status')
        self.sort.addItem('Nearest deadline', 'deadline')
        self.sort.addItem('Furthest behind plan', 'progress')
        self.filters = QWidget()
        f = QHBoxLayout(self.filters)
        f.setContentsMargins(0, 0, 0, 0)
        f.setSpacing(16)
        f.addLayout(self._labelled('Show', self.filter))
        f.addLayout(self._labelled('Sort by', self.sort))
        f.addStretch()
        self.main.addWidget(self.filters)

        self.listEl = QVBoxLayout()
        self.listEl.setSpacing(12)
        self.main.addLayout(self.listEl)
        self.finish()
        # ------------------------------------

        self.greeting.setText('Projects you manage, ' + user['name'].split(' ')[0])

        if not session.isManager():
            self.summaryEl.hide()
            self.filters.hide()
            self.listEl.addWidget(ui.label('The project dashboard is for managers and team leaders. '
                                           'Your own tasks are in My to-do list.', 'notice'))
            return

        try:
            projects = api.getManagerProjects(user['id'])
            self.all = projects
            self.renderSummary(projects)
            self.render()
        except Exception as err:
            ui.showError(self.listEl, err)

        self.filter.currentIndexChanged.connect(self.render)
        self.sort.currentIndexChanged.connect(self.render)

    def _labelled(self, text, widget):
        lay = QVBoxLayout()
        lay.setSpacing(4)
        lay.addWidget(ui.label(text, 'filterLabel'))
        lay.addWidget(widget)
        return lay

    def renderSummary(self, ps):
        needs = len([p for p in ps if p['status'] in ('at_risk', 'behind')])
        stats = [
            {'n': len(ps), 'label': 'Active projects'},
            {'n': needs, 'label': 'Project needs attention' if needs == 1 else 'Projects need attention',
             'tone': 'critical' if needs else ''},
            {'n': sum(p['totals']['overdue'] for p in ps), 'label': 'Overdue tasks'},
            {'n': sum(p['totals']['blocked'] for p in ps), 'label': 'Blocked tasks'},
        ]
        for s in stats:
            tile = QFrame()
            tile.setProperty('class', 'stat' + (' stat--' + s['tone'] if s.get('tone') else ''))
            lay = QVBoxLayout(tile)
            lay.setContentsMargins(16, 14, 16, 14)
            lay.setSpacing(0)
            lay.addWidget(ui.label(str(s['n']), 'stat__n'))
            lay.addWidget(ui.label(s['label'], 'stat__label'))
            self.summaryLay.addWidget(tile, 1)

    def render(self):
        ui.clear(self.listEl)
        filt = self.filter.currentData()
        sort = self.sort.currentData()
        ps = [p for p in self.all
              if filt == 'all' or (filt == 'attention' and p['status'] in ('at_risk', 'behind'))]
        order = {'at_risk': 0, 'behind': 1, 'on_track': 2, 'complete': 3}
        if sort == 'deadline':
            ps.sort(key=lambda p: p['daysLeft'])
        elif sort == 'progress':
            ps.sort(key=lambda p: p['progress']['gap'])
        else:
            ps.sort(key=lambda p: (order[p['status']], p['daysLeft']))

        if not ps:
            self.listEl.addWidget(ui.label('No projects need attention right now. '
                                           'Choose “All projects” to see everything you manage.', 'notice'))
            return
        for p in ps:
            self.listEl.addWidget(self.row(p))

    def row(self, p):
        g = p['progress']['gap']
        gapText = (('Exactly on plan' if g == 0 else f'{g} pts ahead of plan') if g >= 0
                   else f'{abs(g)} pts behind plan')
        frame, lay = ui.panel('project')
        lay.setSpacing(6)

        head = QHBoxLayout()
        name = QPushButton(p['name'])
        name.setProperty('class', 'projectLink')
        name.setCursor(Qt.PointingHandCursor)
        name.clicked.connect(lambda _=False, pid=p['id']: ui.go('project', id=pid))
        head.addWidget(name)
        head.addStretch()
        head.addWidget(ui.statusPill(p['status']))
        lay.addLayout(head)

        lay.addWidget(ui.label(f"{p['team']} team, {p['memberCount']} people. Deadline "
                               f"{ui.fmtDate(p['endDate'])} ({ui.daysLeftText(p['daysLeft'])})", 'project__meta'))
        lay.addSpacing(4)
        bar = Progress(p['progress']['actual'], p['progress']['expected'])
        bar.setAccessibleName(f"{p['progress']['actual']}% of tasks done; plan says {p['progress']['expected']}% by today")
        lay.addWidget(bar)

        foot = QHBoxLayout()
        done = ui.label(f"<b>{p['progress']['actual']}%</b> done, {gapText}", 'lede', rich=True)
        done.setWordWrap(False)
        foot.addWidget(done)
        foot.addStretch()
        t = p['totals']
        counts = ui.label(self.count(t['open'], 'open') + '&nbsp;&nbsp;&nbsp;' +
                          self.count(t['overdue'], 'overdue', t['overdue'] > 0) + '&nbsp;&nbsp;&nbsp;' +
                          self.count(t['blocked'], 'blocked', t['blocked'] > 0), 'lede', rich=True)
        counts.setWordWrap(False)
        foot.addWidget(counts)
        lay.addLayout(foot)
        return frame

    def count(self, n, label, flag=False):
        colour = f" style='color:{T['critical']}'" if flag else ''
        return f'<b{colour}>{n}</b> {label}'


class Progress(QWidget):
    """Progress bar with the 'Plan' marker (div.progress in the web version)."""

    def __init__(self, actual, expected):
        super().__init__()
        self.actual, self.expected = actual, expected
        self.setFixedHeight(36)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        top, h, w = 20, 10, self.width()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(T['track']))
        p.drawRoundedRect(QRectF(0, top, w, h), 5, 5)
        p.setBrush(QColor(T['series-1']))
        p.drawRoundedRect(QRectF(0, top, max(2, self.actual / 100 * w), h), 5, 5)
        x = self.expected / 100 * w
        p.setPen(QPen(QColor(T['ink']), 2))
        p.drawLine(QPointF(x, top - 6), QPointF(x, top + h + 6))
        f = QFont(self.font()); f.setPointSizeF(8)
        p.setFont(f)
        p.setPen(QColor(T['ink-2']))
        p.drawText(QRectF(x - 30, 0, 60, top - 7), Qt.AlignHCenter | Qt.AlignBottom, 'Plan')
        p.end()
