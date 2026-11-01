
import sys
from pathlib import Path

from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QColor
from PySide6.QtUiTools import QUiLoader

from PySide6.QtWidgets import (QApplication,QWidget,QLabel,QDialog,QPushButton,QTableWidget,QTableWidgetItem,
                               QHeaderView,QSizePolicy,)

from workload_data import (WorkLoadManager,User,DATA_FILE,OVER,)

import styles
def refresh_dashboard(window, store, user):
    store.require_manager(user)
    members = store.get_members(user)

    workloads = []
    #Calculates workload for each member 

    for member in members:
        workload = store.workload(user, member.id)
        workloads.append(workload)
    
    total_employees = len(members)
    total_active_tasks = sum(workload.open_tasks for workload in workloads)

    #Displays open hours divided by weekly capacity 

    average_utilisation = (
        sum(w.utilisation for w in workloads) / len(workloads)
        
    )
    #Checks whether employees are overworked by checking their capacity
    overloaded = sum(1 for w in workloads if w.label == OVER)
    # Card Frame Data
    window.findChild(QLabel, "employeeValue").setText(
        str(total_employees)
    )
    window.findChild(QLabel, "taskValue").setText(
            str(total_active_tasks)
    )
    # Rounds percentage
    window.findChild(QLabel, "capacityValue").setText(
            f"{average_utilisation:.0%}"
    )
    window.findChild(QLabel, "overloadedValue").setText(
            str(overloaded)
    )

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

def show_employee_profile(store, user, member):
    # Get employee data
    workload = store.workload(user, member.id)
    tasks = store.get_tasks(user, member.id)

    
    ui_path = Path(__file__).with_name("task_table.ui")
    ui_file = QFile(str(ui_path))

    if not ui_file.open(QFile.OpenModeFlag.ReadOnly):
        raise RuntimeError(f"Cannot open {ui_path}")

    loader = QUiLoader()
    dialog = loader.load(ui_file)
    ui_file.close()

    

   
    dialog.findChild(QLabel, "employeeName").setText(member.name)

    dialog.findChild(QLabel, "openHoursValue").setText(
        f"{workload.open_hours:.1f} / {workload.capacity:.1f} h"
    )

    dialog.findChild(QLabel, "utilisationValue").setText(
        f"{workload.utilisation:.0%}"
    )

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

    dialog.exec()

def create_workload_page():
    ui_path = Path(__file__).with_name("main.ui")
    ui_file = QFile(str(ui_path))

    if not ui_file.open(QFile.OpenModeFlag.ReadOnly):
        raise RuntimeError(f"Cannot open {ui_path}")

    loader = QUiLoader()
    page = loader.load(ui_file)
    ui_file.close()

    if page is None:
        raise RuntimeError(loader.errorString())

    table = page.findChild(QTableWidget, "employeeTable")

    table.setColumnCount(6)
    table.setHorizontalHeaderLabels([
        "Employee", "Assigned Tasks", "Estimated Hours",
        "Capacity", "Utilisation", "Status"
    ])

    table.horizontalHeader().setSectionResizeMode(
        QHeaderView.ResizeMode.Stretch
    )

    store = WorkLoadManager(DATA_FILE)
    user = User(role="MANAGER")

    refresh_dashboard(page, store, user)

    def open_profile(row, column):
        members = store.get_members(user)
        if 0 <= row < len(members):
            show_employee_profile(store, user, members[row])

    table.cellDoubleClicked.connect(open_profile)

    return page

def main():
    
    app = QApplication(sys.argv)

    styles.useTheme(False)
    app.setStyleSheet(styles.stylesheet())

    ui_path = Path(__file__).with_name("main.ui")
    ui_file = QFile(str(ui_path))

    if not ui_file.open(QFile.OpenModeFlag.ReadOnly):
        raise RuntimeError(f"Cannot open UI file: {ui_path}")

    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()

    
    

  
    table = window.findChild(QTableWidget, "employeeTable")
    content = window.findChild(QWidget, "widget")


    if content is not None:
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        if content.layout() is not None:
            content.layout().setSpacing(18)
            content.layout().setContentsMargins(24, 24, 24, 24)


    table.setColumnCount(6)
    table.setHorizontalHeaderLabels([
        "Employee",
        "Assigned Tasks",
        "Estimated Hours",
        "Capacity",
        "Utilisation",
        "Status"
    ])
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


   


    window.setWindowTitle("Workload Monitor")
    window.resize(1100, 700)
    window.setMinimumSize(800, 500)
    store = WorkLoadManager(DATA_FILE)
    user = User(role="MANAGER")

    refresh_dashboard(window, store, user)
    #Connects function to table, opens profile, checks whether profile can be opened 
    def open_profile(row, column):
        members = store.get_members(user)

        if 0 <= row < len(members):
            member = members[row]
            show_employee_profile(store, user, member)

    table.cellDoubleClicked.connect(open_profile)
    
    window.show()

   

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
