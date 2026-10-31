"""
insights.py - R09: organisation insights.   [was js/insights.js + insights.html]
Answers the four questions in the client letter:
  1. How well are tasks allocated?
  2. How well are projects progressing overall?
  3. Are projects resourced to finish in reasonable time?
  4. Where should training be provided?
     Forum (Dilip & Emma, 21 Oct): managers decide training, so this section
     only shows delays and issues per skill area. It never flags or suggests training.
R10: every figure is about teams, projects or skill areas, never a named
person, and groups smaller than config MIN_GROUP are withheld.
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox

import api
import charts
import session
import ui
from api import cfg, jsRound


class InsightsPage(ui.Page):
    def __init__(self):
        super().__init__()

        # --- page header (insights.html) ---
        self.main.addWidget(ui.label('Insights', 'h1'))
        self.main.addWidget(ui.label('How work is spread, how projects are going, whether teams have enough people, '
                                     'and where delays and issues cluster. Figures cover teams, projects and skill areas, '
                                     'never named individuals.', 'lede'))
        self.teamSel = QComboBox()
        self.filters = QWidget()
        f = QVBoxLayout(self.filters)
        f.setContentsMargins(0, 0, 0, 0)
        f.setSpacing(4)
        f.addWidget(ui.label('Team', 'filterLabel'))
        f.addWidget(self.teamSel)
        row = QHBoxLayout()
        row.addWidget(self.filters)
        row.addStretch()
        self.main.addLayout(row)
        self.root = QVBoxLayout()
        self.root.setSpacing(16)
        self.main.addLayout(self.root)
        self.finish()
        # -----------------------------------

        if not session.isManager():
            self.root.addWidget(ui.label('Insights are for managers and team leaders.', 'notice'))
            self.filters.hide()
            return

        self.teamSel.addItem('All teams', 'all')
        for t in api.getTeams():
            self.teamSel.addItem(t['name'], t['id'])
        self.teamSel.currentIndexChanged.connect(self.load)
        self.load()

    def load(self):
        try:
            self.render(api.getInsights(self.teamSel.currentData()))
        except Exception as err:
            ui.showError(self.root, err)

    def render(self, d):
        ui.clear(self.root)
        self.drawAllocation(self.section('Task allocation', self.allocationLead(d['allocation'])), d['allocation'])
        self.drawProgress(self.section('Project progress', self.progressLead(d['progress'])), d['progress'])
        self.drawResourcing(self.section('Resourcing', self.resourcingLead(d['resourcing'])), d['resourcing'])
        self.drawTraining(self.section('Training needs', self.trainingLead(d['training'])), d['training'])

    def section(self, title, lead):
        frame, lay = ui.panel()
        lay.addWidget(ui.label(title, 'h2'))
        lay.addWidget(ui.label(lead, 'finding'))
        lay.addSpacing(6)
        self.root.addWidget(frame)
        return lay

    # ---------- 1. Allocation ----------
    # Open project hours per person, in weeks of that person's own capacity.
    # Personal to-dos are not counted (forum, Dilip & Emma, 21 Oct).
    def allocationLead(self, a):
        if a['suppressed']:
            return f"Hidden: fewer than {cfg['MIN_GROUP']} people in this group."
        even = a['halfHeldByPct'] >= 40
        return (('Work is spread fairly evenly. ' if even else 'Work is concentrated. ') +
                f"Half of the {a['totalOpenHours']:g} open hours sit with {a['halfHeldByPct']}% of the "
                f"{a['headcount']} people. On average each person has {a['averageWeeks']:g} weeks of work queued.")

    def drawAllocation(self, el, a):
        if a['suppressed']:
            el.addWidget(self.suppressedNote())
            return
        charts.columns(el, [{
            'label': b['label'], 'value': b['people'],
            'tip': f"<strong>{b['people']}{' person' if b['people'] == 1 else ' people'}</strong><br>"
                   f"with {b['label'].lower()} of work queued",
        } for b in a['buckets']], {
            'label': 'Number of people by how many weeks of open work they hold',
            'xTitle': 'Open hours ÷ weekly hours (bars show number of people)',
            'table': {'headers': ['Work queued', 'People'], 'rows': [[b['label'], b['people']] for b in a['buckets']]},
        })

    # ---------- 2. Progress ----------
    def progressLead(self, ps):
        behind = [p for p in ps if p['status'] in ('behind', 'at_risk')]
        if not ps:
            return 'No projects in this group.'
        if not behind:
            return f'All {len(ps)} projects are on track against their plan.'
        return f"{len(behind)} of {len(ps)} projects are behind plan: " + ui.listText([p['name'] for p in behind]) + '.'

    def drawProgress(self, el, ps):
        charts.hbars(el, [{
            'label': p['name'], 'value': p['progress']['actual'], 'display': f"{p['progress']['actual']}%",
            'extra': ui.statusPill(p['status']),
            'tip': f"<strong>{ui.esc(p['name'])}</strong><br>{p['progress']['actual']}% done, plan "
                   f"{p['progress']['expected']}%<br>{p['totals']['overdue']} overdue, "
                   f"{ui.esc(ui.daysLeftText(p['daysLeft']).lower())}",
        } for p in ps], {
            'max': 100,
            'table': {'headers': ['Project', 'Done', 'Planned by today', 'Status'],
                      'rows': [[p['name'], f"{p['progress']['actual']}%", f"{p['progress']['expected']}%",
                                ui.STATUS[p['status']]['label']] for p in ps]},
        })

    # ---------- 3. Resourcing ----------
    def resourcingLead(self, rs):
        short = [r for r in rs if r['level'] == 'critical']
        if not short:
            return 'Every project has enough people-time left to clear its open work.'
        return (f"{len(short)}{' project has' if len(short) == 1 else ' projects have'}"
                ' more open work than the team can finish before the deadline.')

    def drawResourcing(self, el, rs):
        labels = {'good': 'Enough', 'warning': 'Tight', 'critical': 'Short'}
        shown = []
        for r in rs:
            pct = 200 if r['ratio'] is None else jsRound(r['ratio'] * 100)
            shown.append({
                'label': r['name'], 'value': min(pct, 200),
                'display': 'Past deadline' if r['ratio'] is None else f'{pct}%',
                'extra': ui.levelPill(r['level'], labels[r['level']]),
                'tip': f"<strong>{ui.esc(r['name'])}</strong><br>{r['demandHours']:g} hours of work open<br>"
                       f"{r['capacityHours']:g} hours available<br>{r['workingDaysLeft']} working days left, "
                       f"{r['blocked']} blocked",
            })
        charts.hbars(el, shown, {
            'max': 200,
            'ref': {'value': 100, 'label': 'Line = 100%: open work exactly fills the time left. Above it, the team is short.'},
            'table': {'headers': ['Project', 'Open hours', 'Hours available', 'Load', 'Blocked'],
                      'rows': [[r['name'], r['demandHours'], r['capacityHours'],
                                'Past deadline' if r['ratio'] is None else f"{jsRound(r['ratio'] * 100)}%", r['blocked']]
                               for r in rs]},
        })
        el.addWidget(ui.label("Hours available = each member's weekly hours up to the deadline, "
                              'split evenly across the projects they are on.', 'small'))

    # ---------- 4. Training (information only) ----------
    # The client doesn't want the system to identify or assign training, so
    # there is no threshold, flag or verdict here. Managers judge from the figures.
    def trainingLead(self, ts):
        visible = sorted([t for t in ts if not t['suppressed']], key=lambda t: t['issueRate'], reverse=True)
        if not visible or visible[0]['issueRate'] == 0:
            return 'No late, reopened or overdue tasks in any skill area shown.'
        top = [t for t in visible[:2] if t['issueRate'] > 0]
        return ('Most delays and issues: ' + ui.listText([f"{t['area']} ({t['issueRate']}%)" for t in top]) +
                '. Use this alongside your knowledge of the team when deciding on training.')

    def drawTraining(self, el, ts):
        visible = sorted([t for t in ts if not t['suppressed']], key=lambda t: t['issueRate'], reverse=True)
        hidden = [t for t in ts if t['suppressed']]
        charts.hbars(el, [{
            'label': t['area'], 'value': t['issueRate'], 'display': f"{t['issueRate']}%",
            'tip': f"<strong>{ui.esc(t['area'])}</strong><br>{t['tasks']} tasks, {t['people']} people<br>"
                   f"{t['late']} finished late, {t['reopened']} reopened, {t['overdue']} overdue now",
        } for t in visible], {
            'max': 100,
            'table': {'headers': ['Skill area', 'Tasks', 'Finished late', 'Reopened', 'Overdue', 'Issue rate'],
                      'rows': [[t['area'], t['tasks'], t['late'], t['reopened'], t['overdue'], f"{t['issueRate']}%"]
                               for t in visible]},
        })
        el.addWidget(ui.label('Issue rate = share of tasks in that area that finished late, were reopened '
                              'or are overdue now.', 'small'))
        if hidden:
            el.addWidget(ui.label('Not shown: ' + ', '.join(t['area'] for t in hidden) +
                                  f". Fewer than {cfg['MIN_GROUP']} people worked on it, so the figure could identify someone.",
                                  'small'))

    def suppressedNote(self):
        return ui.label(f"This figure is hidden because the group has fewer than {cfg['MIN_GROUP']}"
                        ' people, and showing it could identify individuals.', 'lede')