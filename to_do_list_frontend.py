import PySide6.QtWidgets as PQ
from PySide6.QtCore import Qt, QDate

from datetime import date

import styles
import ui
import to_do_list_backend as backend


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


# This is a reusable object which represents a task
def TaskObject(title, dueDate, taskId, delete_task):
        # ui.panel is a resuable function which generates a frame
        task, task_layout = ui.panel()

        # creates a layout to store the text
        text_layout = PQ.QVBoxLayout()
        text_layout.setSpacing(2)
        # adds the text to the layout
        text_layout.addWidget(ui.label(title, "h3"))
        text_layout.addWidget(ui.label(dueDateText(dueDate), "muted"))

        # creates a button for task deletion
        delete_button = buttonObj("X", "iconBtn")
        delete_button.clicked.connect(lambda: delete_task(taskId))

        # creates the overall layout of the frame
        layout = PQ.QHBoxLayout()
        layout.addLayout(text_layout)
        layout.addWidget(delete_button)
        task_layout.addLayout(layout)

        return task


# This is the class which represents the list of tasks
class ListOfTasks(ui.Page):
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
        add_task_button.clicked.connect(add_page)
        header_layout.addWidget(add_task_button)
        self.main.addLayout(header_layout)

        tasks = backend.view_items()
        for task in tasks:
            self.main.addWidget(TaskObject(task["title"], task["dueDate"], task["projectId"], self.delete_task))


    def display_add_page(self):
        ui.clear(self.main)

        self.main.addWidget("Add Task", "h1")
        
        # creates a text box for the title
        self.enter_title = PQ.QLineEdit()

        # creates a box which inputs date
        self.enter_date = PQ.QDateEdit(QDate.currentDate())
        # makes the input process more convinient by only allowing dates
        self.enter_date.setCalendarPopup(True)
        self.enter_date.setDisplayFormat("dd/MM/yyyy")

        # adds the submit button
        submit_button = buttonObj("Submit", "primary")
        submit_button.clicked.connect(submit_task)
        
        # adds a way to get back to the main screen
        cancel_button = buttonObj("Cancel", "secondary")
        cancel_button.clicked.connect(list_page)

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
        page_layout.addWidget(ui.label("Title", "filterlabel"))
        page_layout.addWidget(self.enter_title)
        
        # adds a spacing which separates the widgets
        page_layout.addSpacing(8)
        page_layout.addWidget(ui.label("Due Date", "filterlabel"))
        page_layout.addWidget(self.enter_date)
        
        page_layout.addSpacing(12)
        page_layout.addLayout(button_layout)
        self.main.addWidget(page)


      
    # adds new tasks to the list of tasks
    def addTask(self, title, dueDate):
        # adds the task to the backend
        backend.add_item(title, dueDate, "1234")
        self.loadTasks()

    def loadTasks(self):
        # resets the screen
        for task in self.taskArr:
            # removes the task from the list
            self.task_list_layout.removeWidget(task)
            # schedules the task object for asynchronous deletion so that the script doesn't crash
            task.deleteLater()
        # resets the task array
        self.taskArr = []

        # loads list of tasks into list
        tasks = backend.view_items()
        # iterates through the tasks
        for task in tasks:
            # instantiates class object
            taskObj = TaskObject(task["title"], task["dueDate"], task["projectId"], self.delete_task)
            # saves all the task objects incase of deletion
            self.taskArr.append(taskObj)
            # adds the task to the window
            self.task_list_layout.addWidget(taskObj)

    # deletes a task from the list and reloads the ui
    def delete_task(self, taskId):
        backend.remove_item(taskId)
        self.loadTasks()


# This is the class which represents the page for adding tasks
class AddTaskPage(PQ.QWidget):
    def __init__(self, list_page, submit_task):
        super().__init__()

        page_heading = PQ.QLabel("Add Task")

        # creates a text box with a label saying what it is
        title_label = PQ.QLabel("Title")
        self.enter_title = PQ.QLineEdit()

        # creates a box which inputs date
        date_label = PQ.QLabel("Due Date")
        self.enter_date = PQ.QDateEdit()
        # makes the input process more convinient
        self.enter_date.setCalendarPopup(True)
        self.enter_date.setDisplayFormat("dd/MM/yyyy")

        # adds the submit button
        submit_button = buttonObj("Submit", "primary")
        submit_button.clicked.connect(submit_task)
        
        # adds a way to get back to the main screen
        cancel_button = buttonObj("Cancel", "primary")
        cancel_button.clicked.connect(list_page)

        # creates a layout so that the buttons are displayed horizontal
        button_layout = PQ.QHBoxLayout()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(submit_button)

        # creates a layout for the whole screen
        layout = PQ.QVBoxLayout(self)
        # sets the spacing for the layout
        layout.setSpacing(8)
        # adds all the widget to the layout
        layout.addWidget(page_heading)
        layout.addWidget(title_label)
        layout.addWidget(self.enter_title)
        layout.addWidget(date_label)
        layout.addWidget(self.enter_date)
        layout.addLayout(button_layout)


# This is the root class which is like a container for the different pages of the app
class ToDoWindow(PQ.QMainWindow):
    # initialisation
    def __init__(self):
        super().__init__()
        self.setWindowTitle("To Do List")
        # sets window size
        self.resize(400,500)

        # creates a stacked widget so that you can switch between adding and viewing tasks
        self.stack = PQ.QStackedWidget()
        # adds the pages to the stack
        self.task_list = ListOfTasks(add_page=self.show_add_page)
        self.add_tasks = AddTaskPage(list_page=self.show_list_page, submit_task=self.submit_task)
        self.stack.addWidget(self.task_list)
        self.stack.addWidget(self.add_tasks)
        self.setCentralWidget(self.stack)

    # switches to the add tasks page
    def show_add_page(self):
        self.stack.setCurrentWidget(self.add_tasks)

    # switches to the task list page
    def show_list_page(self):
        self.stack.setCurrentWidget(self.task_list)

    # takes in the inputs from the add task page and adds a task to the list
    def submit_task(self):
        self.task_list.addTask(self.add_tasks.enter_title.text(), self.add_tasks.enter_date.date().toString("yyyy-MM-dd"))
        self.show_list_page()


# opens window on run
if __name__ == "__main__":
    app = PQ.QApplication([])

    #setting up the stylesheet
    styles.useTheme(app.styleHints().colorScheme() == Qt.ColorScheme.Dark)
    app.setStyleSheet(styles.stylesheet() + stylesheet())
    
    window = ToDoWindow()
    window.show()
    # closes the app when the x is clicked
    app.exec()

