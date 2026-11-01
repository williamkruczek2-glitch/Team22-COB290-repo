"""
This is the frontend file for the To-Do List portion of the project (R01)

During initial testing this used a basic json file setup in order to emulate the database which be introduced in part 2.
This code was then adapted to run using mock_data.py
"""


import PySide6.QtWidgets as PQ
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from datetime import date

import styles
import ui
import to_do_list_backend as backend
import session
from mock_data import employees


# extra styling for widgets that aren't included in the others' code 
def stylesheet():
    v = styles.T
    return f"""
    QPushButton[class="primary"] {{ background: {v['accent']}; color: {v['surface']}; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }}
    QPushButton[class="primary"]:hover {{ background: {v['series-1']}; }}
    QPushButton[class="secondary"] {{ background: {v['surface']}; color: {v['ink']}; border: 1px solid {v['rule']}; border-radius: 6px; padding: 8px 16px; }}
    QPushButton[class="secondary"]:hover {{ background: {v['surface-2']}; }}
    QPushButton[class="iconBtn"] {{ background: transparent; color: {v['muted']}; border: none; border-radius: 4px; padding: 4px 8px; font-size: 12pt; }}
    QPushButton[class="iconBtn"]:hover {{ background: {v['surface-2']}; color: {v['critical']}; }}
    QLineEdit, QDateEdit {{ color: {v['ink']}; background: {v['surface']}; border: 1px solid {v['rule']}; border-radius: 6px; padding: 6px 10px; }}
    QLineEdit:focus, QDateEdit:focus {{ border: 1px solid {v['accent']}; }}
    """

# a reusable button blueprint which generates button of different styles
def buttonObj(text, style):
    button = PQ.QPushButton(text)
    # sets the button's style type
    button.setProperty("class", style)
    return button

# sanitises the date so that it is a valid deadline
def dueDateText(dueDate):
    try:
        # generates the number of days until the deadline
        days = (date.fromisoformat(dueDate) - date.today()).days
    except ValueError:
        # returns the unaffected date if it is broken
        return dueDate
    # returns the date and remaining days
    dueDateStr = str(ui.fmtDate(dueDate))+" · "+ str(ui.daysLeftText(days))
    return dueDateStr


# This is a reusable object which represents a task
def TaskObject(title, dueDate, taskId, status, change_status, delete_task):
        # ui.panel is a resuable function which generates a frame
        task, task_layout = ui.panel()

        # creates a layout to store the text
        text_layout = PQ.QVBoxLayout()
        text_layout.setSpacing(2)
        # adds the text to the layout
        text_layout.addWidget(ui.label(title, "h3"))
        text_layout.addWidget(ui.label(dueDateText(dueDate), "h3"))

        # creates a drop down box to show the status of completion
        statusDropDown = PQ.QComboBox()
       
        # iterates through the key-value pairs of the different statuses
        for key, value in ui.TASK_STATUS.items():
            # adds the value to the status
            statusDropDown.addItem(value, key)
        # sets the pointer of the drop down menu to be at the current status
        statusDropDown.setCurrentIndex(statusDropDown.findData(status))

        # activates the status change function when the drop down is interacted with
        statusDropDown.activated.connect(lambda: change_status(taskId, statusDropDown.currentData()))

        # creates a button for task deletion
        delete_button = buttonObj("X", "iconBtn")
        delete_button.clicked.connect(lambda: delete_task(taskId))

        # creates the overall layout of the frame
        layout = PQ.QHBoxLayout()
        layout.addLayout(text_layout)
        layout.addWidget(statusDropDown)
        layout.addWidget(delete_button)
        task_layout.addLayout(layout)

        return task


# This is the class which represents the list of tasks
class ToDoWindow(ui.Page):
    def __init__(self):
        super().__init__()
        self.display_list_page()

    def display_list_page(self):
        # removes everything so there are no duplicates
        ui.clear(self.main)
        
        # this splits the heading and Add Task button up from the actual tasks
        header_layout = PQ.QHBoxLayout()
        # add heading and Add Task button to the header
        header_layout.addWidget(ui.label("My To Do List", "h1"))
        # creates a button so that the user can add tasks
        add_task_button = buttonObj("Add Task", "primary")
        # switches pages
        add_task_button.clicked.connect(self.display_add_page)
        header_layout.addWidget(add_task_button)
        self.main.addLayout(header_layout)

        # Creates a subsection for "To Do" tasks
        self.main.addWidget(ui.label("To Do", "h2"))


        tasks = backend.view_items()
        for task in tasks:
            if task["status"] == "todo":
                if task["assigneeId"] == session.get()["id"]:
                    self.main.addWidget(TaskObject(task["title"], task["dueDate"], task["projectId"], task["status"], self.change_status, self.delete_task))

        self.main.addWidget(ui.label("In Progress", "h2"))

        for task in tasks:
            if task["status"] == "in_progress":
                if task["assigneeId"] == session.get()["id"]:
                    self.main.addWidget(TaskObject(task["title"], task["dueDate"], task["projectId"], task["status"], self.change_status, self.delete_task))

        self.main.addWidget(ui.label("Blocked", "h2"))

        for task in tasks:
            if task["status"] == "blocked":
                if task["assigneeId"] == session.get()["id"]:
                    self.main.addWidget(TaskObject(task["title"], task["dueDate"], task["projectId"], task["status"], self.change_status, self.delete_task))

        self.main.addWidget(ui.label("Done", "h2"))

        for task in tasks:
            if task["status"] == "done":
                if task["assigneeId"] == session.get()["id"]:
                    self.main.addWidget(TaskObject(task["title"], task["dueDate"], task["projectId"], task["status"], self.change_status, self.delete_task))


        self.finish()

    def display_add_page(self):
        ui.clear(self.main)

        self.main.addWidget(ui.label("Add Task", "h1"))
        
        # creates a text box for the title
        self.enter_title = PQ.QLineEdit()

        # creates a box which inputs date
        self.enter_date = PQ.QDateEdit(QDate.currentDate())
        # makes the input process more convinient by only allowing dates
        self.enter_date.setCalendarPopup(True)
        self.enter_date.setDisplayFormat("dd/MM/yyyy")
        self.enter_date.setMinimumDate(QDate.currentDate())

        # adds the submit button
        submit_button = buttonObj("Submit", "primary")
        submit_button.clicked.connect(self.submit_task)
        
        # adds a way to get back to the main screen
        cancel_button = buttonObj("Cancel", "secondary")
        cancel_button.clicked.connect(self.display_list_page)

        # creates a layout so that the buttons are displayed horizontal
        button_layout = PQ.QHBoxLayout()
        
        # spaces the buttons out for better readbility
        button_layout.setSpacing(10)
        button_layout.addStretch(1)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(submit_button)

        # creates a layout for the whole screen
        page, page_layout = ui.panel()
        page.setMaximumWidth(520)
        
        # adds all the widget to the layout
        page_layout.addWidget(ui.label("Title", "filterLabel"))
        page_layout.addWidget(self.enter_title)
        
        # adds a spacing which separates the widgets
        page_layout.addSpacing(8)
        page_layout.addWidget(ui.label("Due Date", "filterLabel"))
        page_layout.addWidget(self.enter_date)

        # checks if the user is a manager 
        if session.get()["role"] == "manager" or session.get()["role"] == "team_leader":
            # creates a text box to input the name of an employee who will be the assignee of the task
            self.enter_assignee = PQ.QLineEdit()
            page_layout.addSpacing(8)
            page_layout.addWidget(ui.label("Assignee Name", "filterLabel"))
            page_layout.addWidget(self.enter_assignee)
        
        page_layout.addSpacing(12)
        page_layout.addLayout(button_layout)
        self.main.addWidget(page)

        self.finish()
  
    # adds new tasks to the list of tasks
    def addTask(self, title, dueDate, assigneeName=None):
        # retrieves the data of the current user
        currentUser = session.get()
        
        # if the user is not a manager/team leader then the task will be assigned to themself by default
        if assigneeName is None:
            assigneeId = currentUser["id"]
        
        # if the user is a manager/team leader then the task will be assigned to the person named in the add task window
        else:
            employeeFound = False
            # iterates through the list of employees until the one with the right name is found
            for employee in employees:
                if employee["name"] == assigneeName:
                    employeeFound = True
                    # checks if the manager or team leader managers the team of the current employee
                    if session.get()["teamId"] == employee["teamId"]:
                        assigneeId = employee["id"]
            if not employeeFound:
                PQ.QMessageBox.warning(self, "Unknown Input", "The employee you have entered does not exist.")
                return
        # adds the task to the backend
        backend.add_item(title, dueDate, assigneeId)
        self.display_list_page()

    # deletes a task from the list and reloads the ui
    def delete_task(self, taskId):
        backend.remove_item(taskId)
        self.display_list_page()

    # takes in the inputs from the add task page and adds a task to the list
    def submit_task(self):
        
        # assigns the task to a different employee if the current user is a manager/team leader
        if session.get()["role"] == "manager" or session.get()["role"] == "team_leader":
            if self.enter_assignee.text() != "":
                self.addTask(self.enter_title.text(), self.enter_date.date().toString("yyyy-MM-dd"), self.enter_assignee.text())
            
            # if the manager/team leader hasn't inputted an employee then the task will be assigned to themself
            else:
                self.addTask(self.enter_title.text(), self.enter_date.date().toString("yyyy-MM-dd"))
        
        # task assigned to the user if they aren't a manager or team leader
        else:
            self.addTask(self.enter_title.text(), self.enter_date.date().toString("yyyy-MM-dd"))
        self.display_list_page()

    def change_status(self, taskId, newStatus):
        backend.change_status(taskId, newStatus)
        self.display_list_page() 

# opens window on run
if __name__ == "__main__":
    app = PQ.QApplication([])

    # setting the styles of the page as a whole
    app.setStyle("Fusion")
    font = QFont()
    font.setFamilies(["Atkinson Hyperlegible", "Segoe UI", "Helvetica Neue", "Arial"])
    app.setFont(font)
    styles.useTheme(app.styleHints().colorScheme() == Qt.ColorScheme.Dark)
    app.setStyleSheet(styles.stylesheet() + stylesheet())
    
    window = PQ.QMainWindow()
    window.resize(900, 640)
    window.setCentralWidget(ToDoWindow())
    window.show()
    # closes the app when the x is clicked
    app.exec()

