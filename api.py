"""
api.py - the "backend" for R02 (manager dashboard) and R09 (insights).   [was js/api.js]

Part 1: functions read db (mock data) and do the calculations here.
Part 2: keep the same function names and return shapes, but replace each
        body with a query to the real database. Pages never touch
        mock_data directly, so nothing else has to change.

No Qt in this file, so it can be checked on its own:  python api.py

Forum replies (Dilip & Emma, 21 Oct):
  - progress and workload use estimated hours, not task counts
  - workload compares hours with each person's capacity (hoursPerWeek)
  - personal to-dos (projectId None) never count towards workload
  - training is information only: no flag or threshold
  - team leaders see the same pages as managers
"""
import copy
from datetime import date as _date, timedelta

from mock_data import db, jsRound

config = {
    'MIN_GROUP': 3,              # R10: never show a figure built from fewer people than this
    'ON_TRACK_GAP': -5,          # progress gap (pts) still counted as on track
    'AT_RISK_GAP': -15,          # gap at or below this = at risk
}
cfg = config

today = _date.fromisoformat(db['today'])


def date(s):
    return _date.fromisoformat(s)


def isOpen(t):
    return t['status'] != 'done'


def isOverdue(t):
    return isOpen(t) and date(t['dueDate']) < today


def reply(data):
    return copy.deepcopy(data)


def byId(arr):
    return {x['id']: x for x in arr}


emp, team = byId(db['employees']), byId(db['teams'])


def tasksOf(pid):
    return [t for t in db['tasks'] if t['projectId'] == pid]


def projectTasks():
    """Assigned project tasks only. Personal to-dos (projectId None) are excluded."""
    return [t for t in db['tasks'] if t['projectId']]


def hours(ts):
    return sum(t['estimateHours'] for t in ts)


def workingDaysBetween(a, b):
    n, cur = 0, a
    while cur < b:
        if cur.weekday() < 5:          # Mon-Fri
            n += 1
        cur += timedelta(days=1)
    return n


# ---------- shared calculation: one project's health ----------
# Progress is weighted by estimated hours, so a 40h task counts ten times a 4h one.
def summarise(p):
    ts = tasksOf(p['id'])
    total = len(ts)
    done = len([t for t in ts if t['status'] == 'done'])
    overdue = len([t for t in ts if isOverdue(t)])
    blocked = len([t for t in ts if t['status'] == 'blocked'])
    totalH = hours(ts)
    doneH = hours([t for t in ts if t['status'] == 'done'])
    dueH = hours([t for t in ts if date(t['dueDate']) <= today])
    pct = jsRound((doneH / totalH) * 100) if totalH else 0
    expected = jsRound((dueH / totalH) * 100) if totalH else 0   # planned progress by today
    gap = pct - expected
    end = date(p['endDate'])
    daysLeft = (end - today).days
    if pct == 100:
        status = 'complete'
    elif daysLeft < 0 or gap <= cfg['AT_RISK_GAP']:
        status = 'at_risk'
    elif gap < cfg['ON_TRACK_GAP']:
        status = 'behind'
    else:
        status = 'on_track'

    return {
        'id': p['id'], 'code': p['code'], 'name': p['name'], 'description': p['description'],
        'manager': emp[p['managerId']]['name'], 'team': team[p['teamId']]['name'],
        'startDate': p['startDate'], 'endDate': p['endDate'], 'daysLeft': daysLeft,
        'memberCount': len(p['memberIds']),
        'totals': {'total': total, 'done': done, 'open': total - done, 'overdue': overdue, 'blocked': blocked},
        'hours': {'total': totalH, 'done': doneH, 'open': totalH - doneH},
        'progress': {'actual': pct, 'expected': expected, 'gap': gap},
        'status': status,
    }


# ======================= R02 - Manager's dashboard =======================

# Part 2: SELECT projects WHERE managerId = ?  (team leaders: WHERE teamId = their team)
def getManagerProjects(managerId):
    me = emp[managerId]
    if me['role'] == 'team_leader':
        mine = [p for p in db['projects'] if p['teamId'] == me['teamId']]
    else:
        mine = [p for p in db['projects'] if p['managerId'] == managerId]
    return reply([summarise(p) for p in mine])


# Part 2: SELECT one project and its tasks
def getProjectDetail(projectId):
    p = next((x for x in db['projects'] if x['id'] == projectId), None)
    if p is None:
        raise ValueError('No project with ID ' + projectId)
    ts = tasksOf(p['id'])
    summary = summarise(p)

    byStatus = [{'status': s, 'count': len([t for t in ts if t['status'] == s])}
                for s in ['todo', 'in_progress', 'blocked', 'done']]

    # Burn-up: weekly planned (hours due) vs actual (hours done), start -> today
    start = date(p['startDate'])
    stop = date(p['endDate']) if date(p['endDate']) < today else today
    points = []
    cur = start
    while cur <= stop:
        points.append(weekPoint(ts, cur))
        cur += timedelta(days=7)
    if not points or (points[-1]['date'] != db['today'] and stop == today):
        points.append(weekPoint(ts, today))

    overdueTasks = [taskView(t) for t in sorted([t for t in ts if isOverdue(t)], key=lambda t: t['dueDate'])]
    upcoming = [taskView(t) for t in sorted(
        [t for t in ts if isOpen(t) and today <= date(t['dueDate']) <= today + timedelta(days=14)],
        key=lambda t: t['dueDate'])]

    summary['byStatus'] = byStatus
    summary['burnup'] = points
    summary['overdueTasks'] = overdueTasks
    summary['upcomingTasks'] = upcoming
    return reply(summary)


def weekPoint(ts, when):
    return {
        'date': when.isoformat(),
        'planned': hours([t for t in ts if date(t['dueDate']) <= when]),
        'actual': hours([t for t in ts if t['completedDate'] and date(t['completedDate']) <= when]),
    }


def taskView(t):
    return {'id': t['id'], 'title': t['title'], 'area': t['area'], 'status': t['status'], 'priority': t['priority'],
            'dueDate': t['dueDate'], 'hours': t['estimateHours'], 'assignee': emp[t['assigneeId']]['name'],
            'daysOverdue': max(0, (today - date(t['dueDate'])).days)}


# ======================= R09 - Organisation insights =======================
# R10 rule: these figures are about teams, projects and skill areas - never
# named people. Any group smaller than MIN_GROUP is withheld.

# Part 2: run the insight queries for one team (or all)
def getInsights(teamId):
    everyone = teamId == 'all' or not teamId
    projs = [p for p in db['projects'] if everyone or p['teamId'] == teamId]
    pids = [p['id'] for p in projs]
    ts = [t for t in db['tasks'] if t['projectId'] in pids]
    people = [e for e in db['employees'] if everyone or e['teamId'] == teamId]

    return reply({
        'scope': 'All teams' if everyone else team[teamId]['name'],
        'allocation': allocation(people),
        'progress': [summarise(p) for p in projs],
        'resourcing': [resourcing(p) for p in projs],
        'training': training(ts),
    })


# Task allocation: open project hours per person, measured in weeks of their
# own capacity (open hours / hoursPerWeek). Personal to-dos are left out.
def allocation(people):
    buckets = [
        {'label': 'Under 1 week', 'min': 0, 'max': 1, 'people': 0},
        {'label': '1–2 weeks', 'min': 1, 'max': 2, 'people': 0},
        {'label': '2–4 weeks', 'min': 2, 'max': 4, 'people': 0},
        {'label': '4+ weeks', 'min': 4, 'max': float('inf'), 'people': 0},
    ]
    open_ = [t for t in projectTasks() if isOpen(t)]
    openH = [hours([t for t in open_ if t['assigneeId'] == e['id']]) for e in people]
    weeks = [h / e['hoursPerWeek'] for h, e in zip(openH, people)]
    for w in weeks:
        for b in buckets:
            if b['min'] <= w < b['max']:
                b['people'] += 1
                break
    if len(people) < cfg['MIN_GROUP']:
        return {'suppressed': True, 'headcount': len(people)}
    srt = sorted(openH, reverse=True)
    totalOpen = sum(srt)
    # Smallest share of people holding half of all open hours
    acc, k = 0, 0
    while k < len(srt) and acc < totalOpen / 2:
        acc += srt[k]
        k += 1
    return {
        'suppressed': False, 'headcount': len(people), 'totalOpenHours': totalOpen,
        'averageWeeks': jsRound(sum(weeks) / len(weeks) * 10) / 10,
        'halfHeldByPct': jsRound((k / len(people)) * 100) if totalOpen else 0,
        'buckets': [{'label': b['label'], 'people': b['people']} for b in buckets],
    }


# Resourcing: open hours vs the members' capacity left before the deadline.
# Each member's weekly hours are split evenly across the active projects they're on.
def projectsOf(eid):
    return [p for p in db['projects'] if eid in p['memberIds'] and date(p['endDate']) >= today]


def resourcing(p):
    open_ = [t for t in tasksOf(p['id']) if isOpen(t)]
    demand = hours(open_)
    end = date(p['endDate'])
    daysLeft = workingDaysBetween(today, end) if end > today else 0
    capacity = sum(emp[m]['hoursPerWeek'] / 5 * daysLeft / max(1, len(projectsOf(m))) for m in p['memberIds'])
    ratio = jsRound((demand / capacity) * 100) / 100 if capacity else None
    if ratio is None:
        level = 'critical' if demand else 'good'
    else:
        level = 'critical' if ratio > 1 else 'warning' if ratio > 0.8 else 'good'
    blocked = [t for t in open_ if t['status'] == 'blocked']
    return {
        'id': p['id'], 'name': p['name'], 'demandHours': demand, 'capacityHours': jsRound(capacity),
        'workingDaysLeft': daysLeft, 'ratio': ratio, 'level': level,
        'pastDeadline': end < today, 'blocked': len(blocked),
    }


# Training needs: per skill area, share of tasks that finished late,
# were reopened, or are overdue now. Information only - managers decide on
# training, so there is no threshold or "training suggested" flag.
def training(ts):
    def finishedLate(t):
        return bool(t['completedDate']) and date(t['completedDate']) > date(t['dueDate'])

    rows = []
    for area in db['areas']:
        at = [t for t in ts if t['area'] == area]
        headcount = len({t['assigneeId'] for t in at})
        if not at:
            continue
        if headcount < cfg['MIN_GROUP']:
            rows.append({'area': area, 'suppressed': True, 'tasks': len(at)})
            continue
        late = len([t for t in at if finishedLate(t)])
        reopened = len([t for t in at if t['reopened']])
        overdue = len([t for t in at if isOverdue(t)])
        issues = len([t for t in at if t['reopened'] or isOverdue(t) or finishedLate(t)])
        rate = issues / len(at)
        rows.append({
            'area': area, 'suppressed': False, 'tasks': len(at), 'people': headcount,
            'late': late, 'reopened': reopened, 'overdue': overdue,
            'issueRate': jsRound(rate * 100),
        })
    rows.sort(key=lambda r: -(r.get('issueRate') or -1))
    return rows


# Part 2: SELECT teams
def getTeams():
    return reply(db['teams'])


if __name__ == '__main__':
    # Quick check without the GUI:  python api.py
    for p in getManagerProjects('E01'):
        print(f"{p['name']:<28} {p['progress']['actual']:>3}% done, plan {p['progress']['expected']:>3}%  {p['status']}")