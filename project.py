"""
project.py - R02 drill-down: one project in detail.   [was js/project.js + project.html]
Burn-up (planned vs completed hours), task status breakdown, overdue and
upcoming tasks. Reached from the dashboard via ui.go('project', id='P1').
"""
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QLabel, QToolTip

import api
import charts
import session
import ui
from styles import T


class ProjectPage(ui.Page):
    def __init__(self, id='P1'):
        super().__init__()

        # --- crumbs (project.html) ---
        crumbs = QHBoxLayout()
        back = QPushButton('Project dashboard')
        back.setProperty('class', 'link')
        back.setCursor(Qt.PointingHandCursor)
        back.clicked.connect(lambda: ui.go('dashboard'))
        self.crumb = ui.label('Project', 'crumbs')
        crumbs.addWidget(back)
        crumbs.addWidget(ui.label('/', 'crumbs'))
        crumbs.addWidget(self.crumb)
        crumbs.addStretch()
        self.main.addLayout(crumbs)
        self.detail = QVBoxLayout()
        self.detail.setSpacing(16)
        self.main.addLayout(self.detail)
        self.finish()
        # ------------------------------

        if not session.isManager():
            self.detail.addWidget(ui.label('Project details are for managers and team leaders.', 'notice'))
            return

        try:
            self.render(api.getProjectDetail(id))
        except Exception as err:
            ui.showError(self.detail, err)

    def render(self, p):
        self.crumb.setText(p['name'])

        statusOrder = ['done', 'in_progress', 'blocked', 'todo']
        counts = {s['status']: s['count'] for s in p['byStatus']}

        # page head
        head = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(ui.label(p['name'], 'h1'))
        left.addWidget(ui.label(p['description'], 'lede'))
        head.addLayout(left, 1)
        head.addWidget(ui.statusPill(p['status']), alignment=Qt.AlignTop)
        self.detail.addLayout(head)

        # facts
        facts = QHBoxLayout()
        facts.setSpacing(16)
        for k, v in [('Done', f"{p['progress']['actual']}% ({p['hours']['done']:g} of {p['hours']['total']:g} h)"),
                     ('Planned by today', f"{p['progress']['expected']}%"),
                     ('Deadline', ui.fmtDate(p['endDate']) + ', ' + ui.daysLeftText(p['daysLeft']).lower()),
                     ('Team', f"{p['team']}, {p['memberCount']} people")]:
            facts.addWidget(self.fact(k, v), 1)
        self.detail.addLayout(facts)

        # progress against plan
        frame, lay = ui.panel()
        lay.addWidget(ui.label('Progress against plan', 'h2'))
        lay.addWidget(ui.label('Estimated hours completed each week compared with hours scheduled to be due.',
                               'panel__sub'))
        charts.burnup(lay, p['burnup'], p['hours']['total'])
        self.detail.addWidget(frame)

        # where the tasks are
        frame, lay = ui.panel()
        lay.addWidget(ui.label(f"Where the {p['totals']['total']} tasks are", 'h2'))
        lay.addWidget(Stack([(s, counts[s], p['totals']['total']) for s in statusOrder]))
        colours = {'done': T['done'], 'in_progress': T['progress'], 'blocked': T['critical'], 'todo': T['todo']}
        stackKey = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'.join(
            f"<span style='color:{colours[s]}'>■</span> {ui.TASK_STATUS[s]} <b>{counts[s]}</b>" for s in statusOrder)
        lay.addWidget(ui.label(stackKey, 'lede', rich=True))
        self.detail.addWidget(frame)

        # overdue / upcoming
        twoCol = QHBoxLayout()
        twoCol.setSpacing(16)
        twoCol.addWidget(self.taskPanel('Overdue', p['overdueTasks'], True, 'Nothing overdue on this project.'), 1)
        twoCol.addWidget(self.taskPanel('Due in the next 14 days', p['upcomingTasks'], False,
                                        'No open tasks due in the next two weeks.'), 1)
        self.detail.addLayout(twoCol)
        self.detail.addWidget(ui.label('Named workload for each team member is on the Team workload page (R03).', 'small'))

    def fact(self, k, v):
        box = QFrame()
        box.setProperty('class', 'fact')
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(ui.label(k, 'small'))
        lay.addWidget(ui.label(v, 'h3'))
        return box

    def taskPanel(self, title, tasks, overdue, empty):
        frame, lay = ui.panel()
        head = QHBoxLayout()
        head.addWidget(ui.label(title, 'h2'))
        badge = ui.label(str(len(tasks)), 'badge')
        badge.setWordWrap(False)
        head.addWidget(badge)
        head.addStretch()
        lay.addLayout(head)
        if tasks:
            rows, bold = [], set()
            for i, t in enumerate(tasks):
                when = (f"{t['daysOverdue']}{' day' if t['daysOverdue'] == 1 else ' days'}" if overdue
                        else ui.fmtDate(t['dueDate']))
                status = ui.TASK_STATUS[t['status']]
                if t['status'] == 'blocked':
                    status = '▲ ' + status
                    bold.add((i, 3))
                rows.append([t['title'] + '\n' + f"{t['area']} · {t['hours']:g} h", t['assignee'], when, status])
            lay.addWidget(charts.makeTable(['Task', 'Assigned to', 'Late by' if overdue else 'Due', 'Status'],
                                           rows, bold))
        else:
            lay.addWidget(ui.label(empty, 'lede'))
        lay.addStretch()
        return frame


class Stack(QWidget):
    """One bar split by task status (div.stack in the web version)."""

    def __init__(self, segments):
        super().__init__()
        self.segments = segments          # [(status, count, total)]
        self.setFixedHeight(22)
        self.setMouseTracking(True)
        self.hits = []

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        colours = {'done': T['done'], 'in_progress': T['progress'], 'blocked': T['critical'], 'todo': T['todo']}
        shown = [s for s in self.segments if s[1]]
        gap = 2
        usable = self.width() - gap * (len(shown) - 1)
        x = 0.0
        self.hits = []
        p.setPen(Qt.NoPen)
        for i, (status, count, total) in enumerate(shown):
            w = count / total * usable
            p.setBrush(QColor(colours[status]))
            p.drawRoundedRect(QRectF(x, 0, w, self.height()), 4, 4)
            if i > 0:
                p.drawRect(QRectF(x, 0, min(4, w), self.height()))          # square inner edges
            if i < len(shown) - 1:
                p.drawRect(QRectF(x + w - min(4, w), 0, min(4, w), self.height()))
            self.hits.append((QRectF(x, 0, w, self.height()),
                              f"<strong>{ui.TASK_STATUS[status]}</strong><br>{count} tasks ({round(count / total * 100)}%)"))
            x += w + gap
        p.end()

    def mouseMoveEvent(self, e):
        for rect, tip in self.hits:
            if rect.contains(e.position()):
                QToolTip.showText(e.globalPosition().toPoint(), tip, self)
                return
        QToolTip.hideText()