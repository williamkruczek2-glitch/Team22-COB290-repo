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
| `auth.py` | Staff email check and password rules. |
| `login.py` | Sign-in and Create account screens, with the live password checklist. |
| `knowledge.py` | Knowledge base which has topics and posts to share company knowledge. |
| `data-protection.md` | Contains data protection rules. |


## Where the team contributes

**Will dashboard and insights tabs**
- `dashboard.py`: the manager's list of projects (R02)
- `insights.py`: task allocation, progress, resourcing, training (R09)

**Alex (R01, to-do lists)**
- Made the code for the backend and frontend of the to-do list
- The code stores the tasks in a dictionary format in to_do_list.json

**Peter (R03, workload)**
- Presented workload information (Hours, Tasks, Productivity) into a neat table
- Managers can reassign tasks to other employees to optimise workflow
- Frontend made entirely with QtDesigner assisted by the workload_data.py backend

**Umar (R04/R05, topics and posts)**
- Uses the same topic names as `areas` in `mock_data.py`. 
- That lets the training-needs chart link to your topics.
- `knowledge.py`: anyone can create open or restricted topics and posts. (R04, R05)  

**Haytham (R06, R07, sign-in and registration)**
- `auth.py`: staff email check and password rules (R06, R07)
- `login.py`: sign-in and Create account screens, with the live password checklist (R06, R07)
- `main.py`: the LOGIN block that opens the sign-in window and calls session.set(user)

**JP (R08, accounts)**
- Show your login window in `main.py`. There's a comment marking the spot.
- After a successful login, call:
  `session.set({'id': 'E01', 'name': 'Dilip Shah', 'role': 'manager', 'teamId': 'T1'})`
- Only users with `role: 'manager'` can see the dashboard and Insights.

**Deandre (R10, data protection)**
- Insights never shows names.
- Any group under 3 people is hidden. That limit is `MIN_GROUP` in `api.py`.
- `data-protection.md`: A markdown file that contains the data protection rules that every page must follow. (R10)
- Privacy notice and acceptance tick-box added to registration (`RegisterView` in `login.py`).

## Part 2 (database)
Only `api.py` changes: each function will query the database instead of reading `mock_data.py`. The pages stay the same.


