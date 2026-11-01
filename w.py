
import sys
from pathlib import Path
from functools import partial # Allows for preset arguments so they dont have to pass them everytime a function is called
from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QColor
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLineEdit, QSpinBox, QDoubleSpinBox, QMessageBox
from workload_data import AccessDenied, InvalidInput, NotFound
from PySide6.QtWidgets import (QApplication,QWidget,QLabel,QDialog,QPushButton,QTableWidget,QTableWidgetItem,
                               QHeaderView,QSizePolicy,QInputDialog)

from workload_data import (WorkLoadManager,User,DATA_FILE,OVER,)
import session
import styles
def load_ui(file):
    path = Path(__file__).with_name(file)
    file = QFile(str(path))

    if not file.open(QFile.OpenModeFlag.ReadOnly):
        raise RuntimeError("Cant Open file")
    loader = QUiLoader()
    window = loader.load(file)
    file.close()

    return window
def refresh_dashboard(window, store, user):
    
    members = store.get_members(user)

    workloads = []
    #Calculates workload for each member 

    for member in members:
        workload = store.workload(user, member.id)
        workloads.append(workload)
    
    total_employees = len(members)
    total_active_tasks = sum(workload.open_tasks for workload in workloads)

    #Displays open hours divided by weekly capacity 
    average_utilisation = (sum(w.utilisation for w in workloads) / len(workloads) if workloads else 0)

    #Checks whether employees are overworked by checking their capacity
    overloaded = sum(1 for w in workloads if w.label == OVER)

    # Card Frame Data
    window.findChild(QLabel, "employeeValue").setText(str(total_employees))
    window.findChild(QLabel, "taskValue").setText(str(total_active_tasks))
    window.findChild(QLabel, "capacityValue").setText(f"{average_utilisation:.0%}")
    window.findChild(QLabel, "overloadedValue").setText(str(overloaded))


    table = window.findChild(QTableWidget, "employeeTable")
    table.setRowCount(len(members))
    #Creates a tuple of members and workloads, then unpacks their values into separate variables
    for row, (member,workload) in enumerate(zip(members,workloads)):
        values = [
            member.name,
            str(workload.open_tasks),
            f"{workload.open_hours:.1f}",
            f"{workload.capacity:.1f}",
            f"{workload.utilisation:.0%}",
            workload.label,
        ]

        #Assigns data to the employeeTable
        for column, value, in enumerate(values):
            item = QTableWidgetItem(value)
            #Aligns values to the center of the column
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if column == 5:
                if workload.label == "Over Capacity":
                    color = styles.T["critical"]
                elif workload.label == "Near Capacity":
                    color = styles.T["warning"]
                else:
                    color = styles.T["good"]
                item.setForeground(QColor(color))

            table.setItem(row,column,item)

    table.verticalHeader().setVisible(False)
def show_add_task(store,user,member):
    dialog = load_ui("add_task.ui")
    save_button = dialog.findChild(QPushButton, "saveTaskButton")
    cancel_button = dialog.findChild(QPushButton, "cancelButton")

    # Saves the arguments for when the button is clicked, without calling the function
    save_button.clicked.connect(partial(save_task,dialog,store,user,member))
    cancel_button.clicked.connect(dialog.reject)

    #Checks whether the task was successfully added    
    return dialog.exec() == QDialog.DialogCode.Accepted

def open_add_task(profile_dialog,store,user,member):
    if show_add_task(store,user,member):
        profile_dialog.accept()

def save_task(dialog,store,user,member):
    #Saves the task when its added
    name = dialog.findChild(QLineEdit, "taskNameInput").text().strip()
    hours = dialog.findChild(QDoubleSpinBox, "hoursInput").value()
    difficulty = dialog.findChild(QSpinBox, "difficultyInput").value()
    try:
        store.add_task(user,name,member.id,difficulty,hours)
        dialog.accept()

    except( AccessDenied, InvalidInput, NotFound) as e:
        QMessageBox.warning(dialog, "Cannot add Task", str(e))

def show_employee_profile(store, user, member):
    # Get employee data
    member = store.view_profile(user, member.id)
    workload = store.workload(user, member.id)
    tasks = store.get_tasks(user, member.id)

    dialog = load_ui("task_table.ui")
    
    dialog.findChild(QLabel, "employeeName").setText(member.name)
    dialog.findChild(QLabel, "openHoursValue").setText(f"{workload.open_hours:.1f} / {workload.capacity:.1f} h")
    dialog.findChild(QLabel, "utilisationValue").setText(f"{workload.utilisation:.0%}")

    status = dialog.findChild(QLabel, "capacityValue")
    status.setText(workload.label)
    if workload.label == "Over Capacity":
        color = styles.T["critical"]
    elif workload.label == "Near Capacity":
        color = styles.T["warning"]
    else:
        color = styles.T["good"]
    status.setStyleSheet(f"color:{color};")

    # Update the task table
    table = dialog.findChild(QTableWidget, "taskTable")
    table.setRowCount(len(tasks))   
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)   

    for row, task in enumerate(tasks):
        values = [
            task.name,
            str(task.est_hours),
            str(task.difficulty),
            task.priority,
            task.status
        ]

        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, col, item)

    # Close button
    dialog.findChild(QPushButton, "closeButton").clicked.connect(
        dialog.reject
    )
    
    add_button = dialog.findChild(QPushButton, "addTaskButton")
    remove_button = dialog.findChild(QPushButton, "removeTask")
    reassign_button = dialog.findChild(QPushButton, "ReassignTask")

    if user.role == "MANAGER":
        add_button.clicked.connect(partial(open_add_task, dialog,store,user,member))
        remove_button.clicked.connect(partial(remove_selected_task,dialog,store,user,tasks))
        reassign_button.clicked.connect(partial(reassign_task,dialog,store,user,tasks))
    else:
        add_button.hide()
        remove_button.hide()
        reassign_button.hide()
    dialog.exec()

  
def make_user(employee):
    if employee["role"] in ("manager", "team_leader"):
        return User(
            role="MANAGER",
            name=employee["name"]
        )
    if employee["id"] == "E03":
        return User(
            role = "EMPLOYEE",
            member_id=7,
            name =employee["name"]
        )
def reassign_task(dialog,store,user,tasks,):
    table = dialog.findChild(QTableWidget, "taskTable")
    row = table.currentRow()
    task = tasks[row]
    members = [
        m for m in store.get_members(user)
        if m.id != task.assigned_id
    ]
    names = [m.name for m in members]
    name, ok = QInputDialog.getItem(
        dialog,
        "Reassign Task",
        f"Reassign {task.name} to :",
        names,
        0,
        False
    )
    index = names.index(name)
    new_member = members[index]
    store.reassign_task(user, new_member.id, task.id)
    dialog.accept()


    
    
def remove_selected_task(dialog,store,user,tasks):
    table = dialog.findChild(QTableWidget, "taskTable")
    row = table.currentRow()
    task = tasks[row]
    store.remove_task(user, task.id)
    dialog.accept()
def setup_table(window):
    table = window.findChild(QTableWidget, ("employeeTable"))

    table.setColumnCount(6)
    table.setHorizontalHeaderLabels(["Employee", "Assigned Tasks", "Estimated Hours","Capacity", "Utilisation", "Status"])

    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    return table

def open_profile(window,store,user,row,column):
    members = store.get_members(user)

    if 0 <=row < len(members):
        show_employee_profile(store,user,members[row])
        refresh_dashboard(window,store,user)

def create_workload_page(employee):
    page = load_ui("main.ui")
    table = setup_table(page)

    store = WorkLoadManager(DATA_FILE)

    user = make_user(employee)
    refresh_dashboard(page, store, user)
    
    table.cellDoubleClicked.connect(partial(open_profile, page, store, user))
    return page
    

def main():
    
    app = QApplication(sys.argv)

    styles.useTheme(False)
    app.setStyleSheet(styles.stylesheet())

    window = create_workload_page({
        "id": "E03",
        "name": "Clara Novak",
        "role": "specialist"
        })
    window.setWindowTitle("Workload Monitor")
    window.resize(1100,700)
    window.setMinimumSize(800,500)

    table = window.findChild(QTableWidget, "employeeTable")
    content = window.findChild(QWidget, "widget")
    if content is not None:
        content.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)

        if content.layout() is not None:
            content.layout().setSpacing(18)
            content.layout().setContentsMargins(24, 24, 24, 24)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
