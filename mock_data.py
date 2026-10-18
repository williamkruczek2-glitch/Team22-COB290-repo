"""
mock_data.py - stand-in for the database (Part 1 has no DB).   [was js/mockData.js]

Every list here mirrors a future table:
  teams, employees, projects, tasks
In Part 2, delete this file and point api.py at the real database.
Dates are generated relative to "today" so the demo always looks current.
A seeded random generator keeps the data identical on every run
(and identical to the old JavaScript version).
"""
import math
from datetime import date, timedelta


# Seeded PRNG (mulberry32) - same output every run, same numbers as the JS version.
def rng(seed):
    state = [seed & 0xFFFFFFFF]
    M = 0xFFFFFFFF

    def imul(a, b):
        return (a * b) & M

    def rand():
        state[0] = (state[0] + 0x6D2B79F5) & M
        s = state[0]
        t = imul(s ^ (s >> 15), 1 | s)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & M) ^ t
        return ((t ^ (t >> 14)) & M) / 4294967296
    return rand


rand = rng(290)


def pick(arr):
    return arr[math.floor(rand() * len(arr))]


def jsRound(x):
    """JavaScript's Math.round (Python's round() rounds 0.5 to even)."""
    return math.floor(x + 0.5)


today = date.today()


def d(offset):
    return today + timedelta(days=offset)


def iso(day):
    return day.isoformat()


# Skill areas line up with the Topics in the client letter (R04),
# so training needs can later link to knowledge-base posts.
areas = ['Software Development', 'Software Issues', 'Printing',
         'Networking', 'Hardware', 'Admin & Procurement']
# Higher = more tasks finish late or get reopened (creates a training signal).
areaDifficulty = {'Software Development': 0.12, 'Software Issues': 0.18,
                  'Printing': 0.38, 'Networking': 0.34, 'Hardware': 0.14, 'Admin & Procurement': 0.08}

teams = [
    {'id': 'T1', 'name': 'Software Development'},
    {'id': 'T2', 'name': 'Infrastructure'},
    {'id': 'T3', 'name': 'Admin & Support'},
]

employees = [
    # Managers - the client's project-manager representatives
    {'id': 'E01', 'name': 'Dilip Shah',      'email': 'dilip.shah@make-it-all.co.uk',   'teamId': 'T1', 'role': 'manager'},
    {'id': 'E02', 'name': 'Emma Clarke',     'email': 'emma.clarke@make-it-all.co.uk',  'teamId': 'T2', 'role': 'manager'},
    # Software Development
    {'id': 'E03', 'name': 'Clara Novak',     'email': 'clara.novak@make-it-all.co.uk',  'teamId': 'T1', 'role': 'specialist'},
    {'id': 'E04', 'name': 'Bert Hughes',     'email': 'bert.hughes@make-it-all.co.uk',  'teamId': 'T1', 'role': 'specialist'},
    {'id': 'E05', 'name': 'Priya Natarajan', 'email': 'priya.n@make-it-all.co.uk',      'teamId': 'T1', 'role': 'specialist'},
    {'id': 'E06', 'name': 'Tom Okafor',      'email': 'tom.okafor@make-it-all.co.uk',   'teamId': 'T1', 'role': 'specialist'},
    {'id': 'E07', 'name': 'Hannah Reid',     'email': 'hannah.reid@make-it-all.co.uk',  'teamId': 'T1', 'role': 'specialist'},
    # Infrastructure
    {'id': 'E08', 'name': 'Luis Moreno',     'email': 'luis.moreno@make-it-all.co.uk',  'teamId': 'T2', 'role': 'specialist'},
    {'id': 'E09', 'name': 'Aisha Begum',     'email': 'aisha.begum@make-it-all.co.uk',  'teamId': 'T2', 'role': 'specialist'},
    {'id': 'E10', 'name': 'Sam Whitaker',    'email': 'sam.whitaker@make-it-all.co.uk', 'teamId': 'T2', 'role': 'specialist'},
    {'id': 'E11', 'name': 'Grace Lin',       'email': 'grace.lin@make-it-all.co.uk',    'teamId': 'T2', 'role': 'specialist'},
    {'id': 'E12', 'name': 'Owen Price',      'email': 'owen.price@make-it-all.co.uk',   'teamId': 'T2', 'role': 'specialist'},
    # Admin & Support
    {'id': 'E13', 'name': 'Alice Morgan',    'email': 'alice.morgan@make-it-all.co.uk', 'teamId': 'T3', 'role': 'manager'},
    {'id': 'E14', 'name': 'Ruth Adeyemi',    'email': 'ruth.adeyemi@make-it-all.co.uk', 'teamId': 'T3', 'role': 'staff'},
    {'id': 'E15', 'name': 'Jack Dawson',     'email': 'jack.dawson@make-it-all.co.uk',  'teamId': 'T3', 'role': 'staff'},
    {'id': 'E16', 'name': 'Mei Chen',        'email': 'mei.chen@make-it-all.co.uk',     'teamId': 'T3', 'role': 'staff'},
    {'id': 'E17', 'name': 'Kofi Mensah',     'email': 'kofi.mensah@make-it-all.co.uk',  'teamId': 'T3', 'role': 'staff'},
]

# health = share of due tasks actually done (drives on-track / behind / at-risk)
projectSeeds = [
    {'id': 'P1', 'code': 'HTM', 'name': 'Helpdesk ticket migration', 'managerId': 'E01', 'teamId': 'T1',
     'start': -60, 'end': 30, 'n': 34, 'health': 0.92, 'members': ['E03', 'E04', 'E05', 'E14', 'E15'],
     'areas': ['Software Development', 'Software Issues', 'Admin & Procurement'],
     'description': 'Move the old email-based helpdesk into the new ticketing workflow.'},
    {'id': 'P2', 'code': 'PFR', 'name': 'Printer fleet refresh', 'managerId': 'E01', 'teamId': 'T2', 'start': -45, 'end': 8,
     'n': 26, 'health': 0.55, 'members': ['E08', 'E09', 'E16'], 'areas': ['Printing', 'Hardware', 'Networking'],
     'description': 'Replace 40 office printers and move them onto managed print queues.'},
    {'id': 'P3', 'code': 'PPU', 'name': 'Payroll portal upgrade', 'managerId': 'E01', 'teamId': 'T1', 'start': -20, 'end': 70,
     'n': 22, 'health': 0.80, 'members': ['E06', 'E07', 'E03', 'E17'], 'areas': ['Software Development', 'Software Issues'],
     'description': 'Upgrade the payroll self-service portal and retire the legacy login.'},
    {'id': 'P4', 'code': 'NSR', 'name': 'Network switch replacement', 'managerId': 'E02', 'teamId': 'T2', 'start': -80, 'end': 5,
     'n': 30, 'health': 0.70, 'members': ['E10', 'E11', 'E12', 'E09'], 'areas': ['Networking', 'Hardware'],
     'description': 'Swap end-of-life switches across both office floors.'},
    {'id': 'P5', 'code': 'NSO', 'name': 'New starter onboarding pack', 'managerId': 'E13', 'teamId': 'T3', 'start': -30, 'end': 45,
     'n': 18, 'health': 0.95, 'members': ['E14', 'E15', 'E16', 'E17'], 'areas': ['Admin & Procurement', 'Printing'],
     'description': 'One checklist and kit for every new starter, from desk to accounts.'},
]

titles = {
    'Software Development': ['Build import script', 'Write API endpoint', 'Add form validation', 'Code review', 'Write unit tests', 'Refactor data model'],
    'Software Issues': ['Fix login timeout', 'Investigate slow query', 'Patch email parser', 'Resolve broken export', 'Triage bug backlog'],
    'Printing': ['Configure print queue', 'Install printer drivers', 'Set up secure release', 'Map floor printers', 'Test duplex defaults'],
    'Networking': ['Update VLAN config', 'Patch switch firmware', 'Run cable survey', 'Configure port security', 'Test failover link'],
    'Hardware': ['Order replacement units', 'Asset-tag new kit', 'Dispose of old units', 'Install rack hardware'],
    'Admin & Procurement': ['Raise purchase order', 'Update supplier list', 'Write user guide', 'Book training room', 'Collect sign-off'],
}

projects, tasks = [], []
taskNo = 1

for s in projectSeeds:
    projects.append({'id': s['id'], 'code': s['code'], 'name': s['name'], 'managerId': s['managerId'], 'teamId': s['teamId'],
                     'startDate': iso(d(s['start'])), 'endDate': iso(d(s['end'])), 'memberIds': s['members'],
                     'description': s['description']})

    for i in range(s['n']):
        area = pick(s['areas'])
        span = s['end'] - s['start']
        dueOff = jsRound(s['start'] + 5 + rand() * (span - 5))
        est = 1 + math.floor(rand() * 5)                # estimate in working days
        createdOff = max(s['start'], dueOff - est - math.floor(rand() * 10))
        isPastDue = dueOff <= 0
        doneChance = s['health'] if isPastDue else s['health'] * 0.22
        done = rand() < doneChance
        difficulty = areaDifficulty[area]
        completed = None

        if done:
            status = 'done'
            late = 1 + math.floor(rand() * 6) if rand() < difficulty else -math.floor(rand() * 3)
            compOff = min(0, dueOff + late)
            completed = iso(d(max(createdOff + 1, compOff)))
        else:
            r = rand()
            status = 'blocked' if r < 0.18 else 'in_progress' if r < 0.6 else 'todo'
            if createdOff > 0:
                status = 'todo'

        tasks.append({
            'id': 'K' + str(taskNo).zfill(3),
            'projectId': s['id'],
            'title': pick(titles[area]),
            'area': area,
            'assigneeId': pick(s['members']),
            'status': status,                        # todo | in_progress | blocked | done
            'priority': pick(['low', 'medium', 'medium', 'high']),
            'estimateDays': est,
            'createdDate': iso(d(createdOff)),
            'dueDate': iso(d(dueOff)),
            'completedDate': completed,
            'reopened': rand() < difficulty * 0.6,   # was marked done, then sent back
        })
        taskNo += 1

db = {'teams': teams, 'employees': employees, 'projects': projects, 'tasks': tasks, 'areas': areas, 'today': iso(today)}
