import PySide6.QtWidgets as PQ
import to_do_list_backend as backend


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
        self.label = PQ.QLabel("To Do List", self)
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


    def addTask(self):
        # stores the text from the text box in a variable
        title = self.textBox.text()
        # stores the date from the date input in a variable
        date = self.dateInput.date()
        # the backend functions are utilised via the UI
        backend.add_item(title, date.toString("yyyy-MM-dd"), "1234")


# opens window on run
if __name__ == "__main__":
    app = PQ.QApplication([])
    window = ToDoWindow()
    window.show()
    # closes the app when the x is clicked
    app.exec()

