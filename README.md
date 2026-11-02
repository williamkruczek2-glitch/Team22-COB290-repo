# Team 22 Make it all prototype

Python desktop version, as the client asked for. Same code and features as the web version, file for file.

**To run:**
1. Install Python 3.10 or newer (python.org). On Windows, tick **"Add Python to PATH"**.
2. Open this folder in VS Code, then open a terminal (`` Ctrl+` ``).
3. Once only:  `pip install -r requirements.txt`
4. Every time:  `python main.py`  (or open `main.py` and press ▶)


## Files
| Python file |  What it does |
|---|---|
| `main.py` | Starts the app. **Run this.** |
| `mock_data.py` | Fake data. Replaced by the database in Part 2. |
| `api.py` | Does the maths. Pages get their data from here. |
| `session.py` | Who is logged in |
| `ui.py` | Shared bits: menu, labels, status pills. |
| `charts.py` | Draws the charts. |
| `dashboard.py` etc. | One file per page. |
| `styles.py` | `css/styles.css` | All the styling and colours. |
| 'auth.py' | Staff email check and password rules. |
| 'login.py' | Sign-in and Create account screens, with the live password checklist. |

## Where the team contributes

**Will dashboard and insights tabs**
- `dashboard.py`: the manager's list of projects (R02)
- `insights.py`: task allocation, progress, resourcing, training (R09)

**Alex (R01, to-do lists)**
- Give your tasks the same fields as `mock_data.py`: `status` (`todo`, `in_progress`, `blocked`, `done`), `dueDate`, `assigneeId`, `projectId`.
- The dashboard then counts them automatically.

**Peter (R03, workload)**
- Named workload per person is your page. My pages only show totals.

**Umar (R04/R05, topics and posts)**
- Use the same topic names as `areas` in `mock_data.py`.
- That lets the training-needs chart link to your topics.

**Haytham & JP (R06–R08, login)**
- Show your login window in `main.py`. There's a comment marking the spot.
- After a successful login, call:
  `session.set({'id': 'E01', 'name': 'Dilip Shah', 'role': 'manager', 'teamId': 'T1'})`
- Only users with `role: 'manager'` can see the dashboard and Insights.

**Deandre (R10, data protection)**
- Insights never shows names.
- Any group under 3 people is hidden. That limit is `MIN_GROUP` in `api.py`.

## Part 2 (database)
Only `api.py` changes: each function will query the database instead of reading `mock_data.py`. The pages stay the same.


