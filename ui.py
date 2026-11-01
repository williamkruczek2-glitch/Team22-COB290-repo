"""
ui.py - small shared helpers: escaping, dates, status labels, nav, page layout.   [was js/ui.js]
Teammates can reuse these when the pages are merged.
"""
import html
from datetime import date

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from PySide6.QtWidgets import (QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout, QScrollArea,
                               QPushButton, QSizePolicy)

import session
from styles import T


def esc(s):
    return html.escape(str(s))


def fmtDate(isoStr):
    d = date.fromisoformat(isoStr)
    return f'{d.day} {d:%b}'          # e.g. "23 Oct"


def daysLeftText(n):
    if n < 0:
        return f"{abs(n)}{' day' if n == -1 else ' days'} past deadline"
    if n == 0:
        return 'Due today'
    return f"{n}{' day' if n == 1 else ' days'} left"


# ['a','b','c'] -> "a, b and c"
def listText(items):
    return ''.join(items) if len(items) < 2 else ', '.join(items[:-1]) + ' and ' + items[-1]


# Status never relies on colour alone: icon + word + colour.
STATUS = {
    'on_track': {'label': 'On track', 'tone': 'good', 'icon': '✓'},
    'behind':   {'label': 'Behind plan', 'tone': 'warning', 'icon': '!'},
    'at_risk':  {'label': 'At risk', 'tone': 'critical', 'icon': '▲'},
    'complete': {'label': 'Complete', 'tone': 'good', 'icon': '✓'},
}
LEVEL = {
    'good':     {'tone': 'good', 'icon': '✓'},
    'warning':  {'tone': 'warning', 'icon': '!'},
    'critical': {'tone': 'critical', 'icon': '▲'},
}
TASK_STATUS = {'todo': 'To do', 'in_progress': 'In progress', 'blocked': 'Blocked', 'done': 'Done'}


class Pill(QWidget):
    """Rounded label: coloured circle with an icon, then a word."""

    def __init__(self, tone, icon, label):
        super().__init__()
        self.tone, self.icon, self.label = tone, icon, label
        self.f = QFont(self.font())
        self.f.setPointSizeF(8.5)
        self.f.setBold(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sizeHint(self):
        return QSize(4 + 18 + 6 + QFontMetrics(self.f).horizontalAdvance(self.label) + 12, 26)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(QColor(T['rule']), 1))
        p.setBrush(QColor(T['surface-2']))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(T[self.tone]))
        circle = QRectF(4, (self.height() - 18) / 2, 18, 18)
        p.drawEllipse(circle)
        p.setFont(self.f)
        p.setPen(QColor('#1b2733' if self.tone == 'warning' else '#ffffff'))
        small = QFont(self.f); small.setPointSizeF(7); p.setFont(small)
        p.drawText(circle, Qt.AlignCenter, self.icon)
        p.setFont(self.f)
        p.setPen(QColor(T['ink']))
        p.drawText(QRectF(28, 0, self.width() - 28, self.height()), Qt.AlignVCenter, self.label)
        p.end()


def pill(tone, icon, label):
    return Pill(tone, icon, label)


def statusPill(status):
    s = STATUS[status]
    return pill(s['tone'], s['icon'], s['label'])


def levelPill(level, label):
    lv = LEVEL[level]
    return pill(lv['tone'], lv['icon'], label)


# ---------------------------------------------------------------------------
# Building blocks that stand in for HTML elements
# ---------------------------------------------------------------------------
def label(text, cls=None, rich=False):
    """A text label. cls works like a CSS class (see styles.py): h1, h2, lede, muted, small..."""
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.RichText if rich else Qt.PlainText)
    if cls:
        lbl.setProperty('class', cls)
    return lbl


def panel(cls='panel'):
    """A white box (like <section class="panel">). Returns (frame, layout)."""
    frame = QFrame()
    frame.setProperty('class', cls)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(8)
    return frame, lay


def clear(layout):
    """Empty a layout (like el.innerHTML = '')."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


class Page(QScrollArea):
    """Base class for a page. Add widgets to self.main (like <main>)."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        outer = QWidget()
        outer.setObjectName('content')
        row = QHBoxLayout(outer)
        row.setContentsMargins(36, 28, 36, 48)
        inner = QWidget()
        inner.setMaximumWidth(1100)
        self.main = QVBoxLayout(inner)
        self.main.setContentsMargins(0, 0, 0, 0)
        self.main.setSpacing(16)
        row.addWidget(inner)
        self.setWidget(outer)

    def finish(self):
        self.main.addStretch()


# Navigation: main.py sets this so pages can move between each other.
_navigate = None


def go(page, **params):
    """Open another page, e.g. go('project', id='P1') - like a link to project.html?id=P1."""
    _navigate(page, **params)


# Left-hand navigation. Links to teammates' pages are placeholders until merge weekend.
NAV_ITEMS = [
    {'key': 'todo', 'label': 'My to-do list', 'owner': 'R01'},
    {'key': 'dashboard', 'label': 'Project dashboard', 'managerOnly': True},
    {'key': 'workload', 'label': 'Team workload', 'owner': 'R03'},
    {'key': 'knowledge', 'label': 'Knowledge base', 'owner': 'R04/R05'},
    {'key': 'insights', 'label': 'Insights', 'managerOnly': True},
]


def renderNav(active):
    user = session.get()
    nav = QFrame()
    nav.setObjectName('nav')
    nav.setFixedWidth(232)
    lay = QVBoxLayout(nav)
    lay.setContentsMargins(14, 20, 14, 20)
    lay.setSpacing(2)

    brand = QHBoxLayout()
    mark = QLabel('M')
    mark.setObjectName('brandMark')
    mark.setFixedSize(30, 30)
    mark.setAlignment(Qt.AlignCenter)
    name = QLabel('Make-It-All')
    name.setObjectName('brand')
    brand.addWidget(mark)
    brand.addSpacing(6)
    brand.addWidget(name)
    brand.addStretch()
    lay.addLayout(brand)
    lay.addSpacing(22)

    for i in NAV_ITEMS:
        if i.get('managerOnly') and not session.isManager():      # managers and team leaders
            continue
        link = QPushButton(i['label'])
        link.setObjectName('navLink')
        link.setCursor(Qt.PointingHandCursor)
        link.setProperty('current', i['key'] == active)
        if i.get('owner'):
            link.setProperty('placeholder', True)
            link.setToolTip('Merged in from ' + i['owner'])
        link.clicked.connect(lambda _=False, k=i['key']: go(k))
        lay.addWidget(link)

    lay.addStretch()
    initials = ''.join(part[0] for part in user['name'].split())
    who = QHBoxLayout()
    avatar = QLabel(initials)
    avatar.setObjectName('avatar')
    avatar.setFixedSize(34, 34)
    avatar.setAlignment(Qt.AlignCenter)
    role = {'manager': 'Project manager', 'team_leader': 'Team leader'}.get(user['role'], 'Staff')
    text = QLabel(f"<b>{esc(user['name'])}</b><br><span style='color:#a9b8c7'>{role}</span>")
    who.addWidget(avatar)
    who.addSpacing(6)
    who.addWidget(text)
    who.addStretch()
    lay.addLayout(who)
    return nav


def showError(layout, err):
    clear(layout)
    layout.addWidget(label(f"Couldn’t load this view: {err}. Restart the app to try again.",
                           'notice notice--error'))