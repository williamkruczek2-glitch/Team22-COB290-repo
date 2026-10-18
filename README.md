# Manager dashboard (R02) + Insights (R09)

**To run:** open `index.html` in a browser. Nothing to install.

## Pages
- `dashboard.html`: the manager's list of projects (R02)
- `project.html`: one project in detail (R02)
- `insights.html`: task allocation, progress, resourcing, training (R09)

## Files
| File | What it does |
|---|---|
| `js/mockData.js` | Fake data. Gets replaced by the database in Part 2. |
| `js/api.js` | Does the maths. Pages get their data from here. |
| `js/session.js` | Who is logged in (Dilip, hardcoded for now). |
| `js/ui.js` | Shared bits: menu, labels, tooltips. |
| `js/charts.js` | Draws the charts. |
| `js/dashboard.js` etc. | One file per page. |
| `css/styles.css` | All the styling and colours. |

## Where your part plugs in

**Everyone**
- To get the same menu and look on your page, copy the `<head>` and `<script>` lines from `dashboard.html`.
- To make your page appear in the menu, put its filename in `js/ui.js` under `renderNav`.

**Alex (R01, to-do lists)**
- Give your tasks the same fields as `mockData.js`: `status` (`todo`, `in_progress`, `blocked`, `done`), `dueDate`, `assigneeId`, `projectId`.
- The dashboard then counts them automatically.

**Peter (R03, workload)**
- Named workload per person is your page. My pages only show totals.

**Umar (R04/R05, topics and posts)**
- Use the same topic names as `areas` in `mockData.js`.
- That lets the training-needs chart link to your topics.

**Haytham (R06–R08, login)**
- After a successful login, call:
  `MIA.session.set({ id: 'E01', name: 'Dilip Shah', role: 'manager', teamId: 'T1' })`
- Only users with `role: 'manager'` can see the dashboard and Insights.

**Deandre (R10, data protection)**
- Insights never shows names.
- Any group under 3 people is hidden. That limit is `MIN_GROUP` in `js/api.js`.

## Part 2 (database)
Only `js/api.js` changes: each function will fetch from the database instead of reading `mockData.js`. The pages stay the same.

## Waiting on the client
These numbers are guesses for now. They're in `MIA.config` at the top of `js/api.js`, so each one is a one-line change.
- How much of each person's time goes to one project? (0.5)
- When should a project count as behind (−5 pts) or at risk (−15 pts)?
- What rate of late or reopened tasks means training is needed? (40%)
