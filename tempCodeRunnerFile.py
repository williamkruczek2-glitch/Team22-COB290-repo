"""
main.py - RUN THIS FILE to start the app.   [was index.html]
    python main.py      (or open this file in VS Code and press ▶)

The window is the left-hand nav plus one page at a time. ui.go('insights')
swaps the page, like clicking a link to insights.html did in the web version.
"""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout

import styles
import ui
from dashboard import DashboardPage
from project import ProjectPage
from insights import InsightsPage

from knowledge import KnowledgePage #from r04/r05


class PlaceholderPage(ui.Page):
    """Stand-in for a teammate's page until merge weekend."""

    def __init__(self, title, owner):
        super().__init__()
        self.main.addWidget(ui.label(title, 'h1'))
        self.main.addWidget(ui.label(f'Merged in from {owner}.', 'lede'))
        self.finish()


# Page name -> what to build. TEAMMATES: swap your placeholder for your page class.
PAGES = {
    'todo':      lambda **_: PlaceholderPage('My to-do list', 'R01'),
    'dashboard': lambda **_: DashboardPage(),
    'project':   lambda id='P1', **_: ProjectPage(id),
    'workload':  lambda **_: PlaceholderPage('Team workload', 'R03'),
    'knowledge': lambda **_: KnowledgePage(),
    'insights':  lambda **_: InsightsPage(),
}
# Which menu item is highlighted for each page (project.py highlights the dashboard).
NAV_KEY = {'project': 'dashboard'}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1280, 860)
        self.root = QWidget()
        self.root.setObjectName('main')
        self.lay = QHBoxLayout(self.root)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)
        self.setCentralWidget(self.root)
        ui._navigate = self.navigate

    def navigate(self, page, **params):
        ui.clear(self.lay)
        self.setWindowTitle({'dashboard': 'Project dashboard', 'insights': 'Insights'}.get(page, 'Make-It-All')
                            + ' – Make-It-All')
        self.lay.addWidget(ui.renderNav(NAV_KEY.get(page, page)))
        self.lay.addWidget(PAGES[page](**params), 1)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')                       # looks the same on Windows and Mac
    font = QFont()
    font.setFamilies(['Atkinson Hyperlegible', 'Segoe UI', 'Helvetica Neue', 'Arial'])
    font.setPointSizeF(10.5)
    app.setFont(font)
    styles.useTheme(app.styleHints().colorScheme() == Qt.ColorScheme.Dark)
    app.setStyleSheet(styles.stylesheet())

    # LOGIN (R06-R08) goes here: show the login window first, and on success
    # call session.set(user). Until then session.py has a hardcoded user.

    window = MainWindow()
    import session
    window.navigate('dashboard' if session.isManager() else 'todo')
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
