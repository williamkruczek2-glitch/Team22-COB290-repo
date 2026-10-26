import PySide6.QtWidgets as PQ
import to_do_list_backend as backend

# This is a reusable object which represents a task
class TaskObject(PQ.QFrame):
    def __init__(self, title, dueDate):
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
        #delete_button.clicked.connect(deleteTask())

        # creates the overall layout of the frame
        layout = PQ.QHBoxLayout()
        layout.addLayout(text_layout)
        layout.addWidget(delete_button)

        # sets the layout for the task
        self.setLayout(layout)

# This is the class which represents the list of tasks
class ListOfTasks(PQ.QWidget):
    def __init__(self):
        super().__init__()

        # creates a heading object
        page_heading = PQ.QLabel("My To Do List")

        # creates a button so that the user can add tasks
        add_task_button = PQ.QPushButton("Add Task")

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

        self.loadTasks()
        
    # adds new tasks to the list of tasks
    def addTask(self, title, dueDate):
        # adds the task to the backend
        backend.add_item(title, dueDate, "1234")
        self.loadTasks()

    def loadTasks(self):
        # loads list of tasks into list
        tasks = backend.view_items()
        # iterates through the tasks
        for task in tasks:
            print(task["title"])
            # instantiates class object
            taskObj = TaskObject(task["title"], task["dueDate"])
            # adds the task to the window
            self.task_list_layout.addWidget(taskObj)

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
        # adds the tasks list to the stack
        self.task_list = ListOfTasks()
        self.stack.addWidget(self.task_list)
        self.setCentralWidget(self.stack)


# opens window on run
if __name__ == "__main__":
    app = PQ.QApplication([])
    window = ToDoWindow()
    window.show()
    # closes the app when the x is clicked
    app.exec()

