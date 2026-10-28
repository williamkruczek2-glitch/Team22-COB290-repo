import PySide6.QtWidgets as PQ
from PySide6.QtCore import Qt
import styles
import to_do_list_backend as backend


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


# This is a reusable object which represents a task
class TaskObject(PQ.QFrame):
    def __init__(self, title, dueDate, taskId, delete_task):
        super().__init__()
        # creates a layout to store the text
        text_layout = PQ.QVBoxLayout()

        
        # creates the text to display the title of the task
        title_label = PQ.QLabel(title)
        # creates the text to display the due date of the task
        due_label = PQ.QLabel(dueDate)
        # adds the text to the layout
        text_layout.addWidget(title_label)
        text_layout.addWidget(due_label)

        # creates a button for task deletion
        delete_button = PQ.QPushButton("X")
        delete_button.clicked.connect(lambda: delete_task(taskId))

        # creates the overall layout of the frame
        layout = PQ.QHBoxLayout()
        layout.addLayout(text_layout)
        layout.addWidget(delete_button)

        # sets the layout for the task
        self.setLayout(layout)


# This is the class which represents the list of tasks
class ListOfTasks(PQ.QWidget):
    def __init__(self, add_page):
        super().__init__()

        # creates a heading object
        page_heading = PQ.QLabel("My To Do List")

        # creates a button so that the user can add tasks
        add_task_button = PQ.QPushButton("Add Task")
        # switches pages
        add_task_button.clicked.connect(add_page)

        # this splits the heading and Add Task button up from the actual tasks
        header_layout = PQ.QHBoxLayout()
        # add heading and Add Task button to the header
        header_layout.addWidget(page_heading)
        header_layout.addWidget(add_task_button)

        # encapsulates the tasks in a container which is easier to deal with
        container = PQ.QWidget()
        
        # creates a layout for the list of tasks
        self.task_list_layout = PQ.QVBoxLayout(container)
        self.task_list_layout.setSpacing(10)
        
        # makes it so that the list is scrollable
        scroll = PQ.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        # creates the layout for the whole page
        full_layout = PQ.QVBoxLayout(self)
        # separates the header and task list
        full_layout.setSpacing(16)
        full_layout.addLayout(header_layout)
        full_layout.addWidget(scroll)

        # initialises the array for task objects
        self.taskArr = []

        # loads the tasks from the flat file into the frontend via the backend
        self.loadTasks()
        
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
        submit_button = PQ.QPushButton("Submit")
        submit_button.clicked.connect(submit_task)
        
        # adds a way to get back to the main screen
        cancel_button = PQ.QPushButton("Cancel")
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

