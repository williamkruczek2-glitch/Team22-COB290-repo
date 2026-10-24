import PySide6.QtWidgets as PQ
import to_do_list_backend as backend



# This is the class which represents the list of tasks
class ListOfTasks(PQ.QWidget):
    def __init__(self):
        super().__init__()

        # creates a heading object
        page_heading = PQ.QLabel("My To Do List")

        # creates a button so that the user can add tasks
        add_task_button = PQ.QPushButton("Add Task")
        

# This is the root class which is like a container for the different pages of the app
class ToDoWindow(PQ.QMainWindow):
    # initialisation
    def __init__(self):
        super().__init__()
        self.setWindowTitle("To Do List")
        # sets window size
        self.resize(400,500)
        
        # creates a container so multiple widgets can exist
        container = PQ.QWidget()
        self.setCentralWidget(container)
        # initialises layout
        layout = PQ.QVBoxLayout()
        container.setLayout(layout)

        # creates display text
        self.label = PQ.QLabel(self.viewTasks(), self)
        # displays text on the screen
        layout.addWidget(self.label)

        # creates a text box
        self.textBox = PQ.QLineEdit(self)
        layout.addWidget(self.textBox)

        # creates a input for dates
        self.dateInput = PQ.QDateEdit(self)
        layout.addWidget(self.dateInput)

        # creates a button
        self.button = PQ.QPushButton("Add Task")
        # adds functionality to the button
        self.button.clicked.connect(self.addTask)
        # displays the button
        layout.addWidget(self.button)
        self.setLayout(layout)


    def taskView(self):
            # stores the text from the text box in a variable
            title = self.textBox.text()
            # stores the date from the date input in a variable
            date = self.dateInput.date()
            # the backend functions are utilised via the UI
            backend.add_item(title, date.toString("yyyy-MM-dd"), "1234")
            # dynamically updates the text on the screen when a new task is added
            self.label.setText(self.viewTasks())

    '''def addTask(self):
        # stores the text from the text box in a variable
        title = self.textBox.text()
        # stores the date from the date input in a variable
        date = self.dateInput.date()
        # the backend functions are utilised via the UI
        backend.add_item(title, date.toString("yyyy-MM-dd"), "1234")
        # dynamically updates the text on the screen when a new task is added
        self.label.setText(self.viewTasks())'''

    def viewTasks(self):
        # fetches the tasks from the backend
        taskArr = backend.view_items()
        taskStr = ""
        # converts array of tasks into a string
        for task in taskArr:
            taskStr += str(task["title"]) + " | " + str(task["dueDate"]) + " | " + str(task["status"])+ "\n"
        return taskStr


# opens window on run
if __name__ == "__main__":
    app = PQ.QApplication([])
    window = ToDoWindow()
    window.show()
    # closes the app when the x is clicked
    app.exec()

