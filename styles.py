"""
styles.py - shared styles for R02 (dashboard) and R09 (insights).   [was css/styles.css]
Colours are tokens so the merged app can share one theme.
Dark mode follows the computer's setting, like the web version.
"""

LIGHT = {
    'page': '#eef1f4', 'surface': '#fcfcfb', 'surface-2': '#f4f6f8',
    'ink': '#1b2733', 'ink-2': '#4f5b67', 'muted': '#6b7682', 'rule': '#d9dee3', 'track': '#e3e7eb',
    'accent': '#1c5cab', 'series-1': '#2a78d6', 'done': '#256abf', 'progress': '#86b6ef', 'todo': '#cfd5db',
    'good': '#0ca30c', 'warning': '#fab219', 'critical': '#d03b3b',
    'nav-bg': '#17324f', 'nav-ink': '#e6edf4',
}
DARK = dict(LIGHT, **{
    'page': '#0f1419', 'surface': '#1a1f25', 'surface-2': '#222830',
    'ink': '#eef1f4', 'ink-2': '#c3cad2', 'muted': '#98a2ad', 'rule': '#333b44', 'track': '#2c333b',
    'accent': '#86b6ef', 'series-1': '#3987e5', 'done': '#3987e5', 'progress': '#1c5cab', 'todo': '#4a535d',
    'nav-bg': '#111d2a',
})

# The active colour set. Charts read from this when they draw.
T = dict(LIGHT)


def useTheme(dark):
    T.clear()
    T.update(DARK if dark else LIGHT)


def stylesheet():
    v = T
    return f"""
* {{ color: {v['ink']}; }}
QMainWindow, #main, QScrollArea {{ background: {v['page']}; border: none; }}
QWidget#content {{ background: {v['page']}; }}
a {{ color: {v['accent']}; }}

/* ---------- left-hand navigation ---------- */
#nav {{ background: {v['nav-bg']}; }}
#nav QLabel {{ color: {v['nav-ink']}; }}
#brand {{ font-weight: bold; font-size: 13pt; }}
#brandMark {{ background: #fab219; color: #17324f; border-radius: 7px; font-weight: bold; }}
#navLink {{ color: {v['nav-ink']}; background: transparent; border: none; text-align: left; padding: 8px 10px; border-radius: 6px; }}
#navLink:hover {{ background: rgba(255,255,255,0.08); }}
#navLink[current="true"] {{ background: rgba(255,255,255,0.14); font-weight: bold; border-left: 3px solid #fab219; }}
#navLink[placeholder="true"] {{ color: #8b9cb0; }}
#avatar {{ background: #2a4a6d; border-radius: 17px; font-weight: bold; }}
#nav QLabel[class="muted"] {{ color: #a9b8c7; }}

/* ---------- text ---------- */
QLabel[class="h1"] {{ font-size: 20pt; font-weight: bold; }}
QLabel[class="h2"] {{ font-size: 13pt; font-weight: bold; }}
QLabel[class="h3"] {{ font-size: 11.5pt; font-weight: bold; }}
QLabel[class="lede"], QLabel[class="finding"], QLabel[class="panel__sub"] {{ color: {v['ink-2']}; }}
QLabel[class="muted"], QLabel[class="project__meta"], QLabel[class="crumbs"] {{ color: {v['muted']}; }}
QLabel[class="small"] {{ color: {v['muted']}; font-size: 9pt; }}
QLabel[class="notice"] {{ background: {v['surface']}; border: 1px solid {v['rule']}; border-radius: 6px; padding: 16px; color: {v['ink-2']}; }}
QLabel[class="notice notice--error"] {{ background: {v['surface']}; border: 1px solid {v['rule']}; border-left: 3px solid {v['critical']}; border-radius: 6px; padding: 16px; }}

/* ---------- panels ---------- */
QFrame[class="panel"], QFrame[class="project"] {{ background: {v['surface']}; border: 1px solid {v['rule']}; border-radius: 6px; }}
QFrame[class="panel"] QLabel, QFrame[class="project"] QLabel {{ background: transparent; border: none; }}

QFrame[class="fact"] {{ border: none; border-left: 3px solid {v['rule']}; }}
QFrame[class="fact"] QLabel {{ border: none; }}

/* ---------- summary stats ---------- */
#summary {{ background: {v['rule']}; border: 1px solid {v['rule']}; border-radius: 6px; }}
QFrame[class="stat"] {{ background: {v['surface']}; }}
QFrame[class="stat stat--critical"] {{ background: {v['surface']}; border-top: 3px solid {v['critical']}; }}
QLabel[class="stat__n"] {{ font-size: 21pt; font-weight: bold; }}
QLabel[class="stat__label"] {{ color: {v['ink-2']}; }}

/* ---------- controls ---------- */
QLabel[class="filterLabel"] {{ color: {v['ink-2']}; font-size: 9.5pt; }}
QComboBox {{ color: {v['ink']}; background: {v['surface']}; border: 1px solid {v['rule']}; border-radius: 6px; padding: 6px 10px; min-width: 170px; }}
QComboBox QAbstractItemView {{ background: {v['surface']}; color: {v['ink']}; selection-background-color: {v['surface-2']}; }}
QPushButton[class="link"] {{ border: none; background: transparent; color: {v['accent']}; text-align: left; padding: 0; }}
QPushButton[class="link"]:hover {{ text-decoration: underline; }}
QPushButton[class="projectLink"] {{ border: none; background: transparent; color: {v['ink']}; font-size: 11.5pt; font-weight: bold; text-align: left; padding: 0; }}
QPushButton[class="projectLink"]:hover {{ color: {v['accent']}; text-decoration: underline; }}

/* ---------- tables ---------- */
QTableWidget {{ background: transparent; border: none; color: {v['ink']}; }}
QHeaderView {{ background: {v['surface']}; border: none; }}
QHeaderView::section {{ background: {v['surface']}; color: {v['muted']}; border: none; border-bottom: 1px solid {v['rule']}; padding: 6px 8px; font-weight: bold; font-size: 9pt; }}
QTableWidget::item {{ border-bottom: 1px solid {v['rule']}; }}
QFrame[class="panel"] QLabel[class="badge"] {{ background: {v['surface-2']}; border: 1px solid {v['rule']}; border-radius: 10px; padding: 0 7px; font-size: 9pt; }}

QToolTip {{ background: {v['surface']}; color: {v['ink']}; border: 1px solid {v['rule']}; padding: 6px 8px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: {v['rule']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""
