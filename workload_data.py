# Managers should be able to view individual employees' workloads to support
# task allocation and resource management.

# We would like workload information to consider estimated hours and employee
# capacity, not just task counts.

# However, this information must be protected against misuse and should not
# be used to unfairly target individual employees.

import csv
from datetime import *
import json 
from pathlib import Path
from dataclasses import *

DATA_FILE = Path(__file__).parent / "data" / "team_data.json"

MANAGER = "MANAGER"
EMPLOYEE = "EMPLOYEE"
STATUS = ("todo", "in-progress", "done")
PRIORITY = ("low", "medium", "high")
AUTOSAVE = True
NEAR_CAPACITY = 0.8
AT_CAPACITY = 1 
OVER = "Over Capacity"
NEAR = "Near Capacity"
LOW = "Has Capacity"

class DataError(Exception): pass
class NotFound(Exception): pass
class AccessDenied(Exception): pass
class InvalidInput(Exception): pass
    #CLASSES
@dataclass(frozen = True) # Initialises fields 
class Member : 
    id : int
    name : str
    weekly_hours : float = 38

@dataclass(frozen = True) 
class Task:
    id : int
    name : str
    assigned_id : int
    est_hours : float
    difficulty: int 
    priority : str = "medium"
    status : str = "todo"
    due: str | None = None

    def __post_init__(self):
        if not self.name.strip():
            raise InvalidInput("Task needs a title")
        if self.est_hours <= 0:
            raise InvalidInput("Estimated hours for a task must be above 0")
        if not isinstance(self.difficulty, int) or not 1 <= self.difficulty <= 10:
            raise InvalidInput("Difficulty must be between 1 and 10")

@dataclass(frozen = True)
class User :
    role : str  
    member_id : int | None = None
    name : str = "Manager"
@dataclass
class AuditEntry :
    time : str
    name : str
    action : str 
    target_id : str
    target_name : str

    #Displays utilisation for 

def status_label(utilisation):
        if utilisation > AT_CAPACITY:
            return OVER
        if utilisation >= NEAR_CAPACITY:
            return NEAR
        else: 
            return LOW 
        
@dataclass(frozen=True)
class Workload :
    member_id : int
    open_hours : float
    open_tasks : int
    capacity : float
    utilisation : float
    label : str
    

class  WorkLoadManager : 
    def __init__(self, data_file):
        self._data_file = data_file
        self._members = []
        self._tasks = []
        self._audit = []
        self.load_data()

        self._audit_file = Path(data_file).with_name("audit_file.csv")
        self.load_audit()
    # FILES 
    #Ensures the same audit file is used per opening of the app
    def load_audit(self):
        if not self._audit_file.exists():
            return
        with open(self._audit_file ,"r", newline="") as u:
            reader = csv.DictReader(u)

            for row in reader:
                #Appends the audit with unpacked dictionaries of data
                self._audit.append(AuditEntry(**row))

    def load_data(self):
        try:
            with open(self._data_file, encoding = "utf-8") as d:
                raw = json.load(d)
            #Unpacks the dictionary, assigns values to new member objects for every member
            #Does the same for tasks 
            members = [Member(**m) for m in raw["members"]]
            tasks = [Task(**t) for t in raw["tasks"]]
        except FileNotFoundError:
            raise DataError(f"Data file not found: {self._data_file}")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise DataError(f"Data file is invalid: {e}")
        self._members, self._tasks = members, tasks

    def _save(self):
        if not AUTOSAVE:
            return
        raw = {"members": [asdict(m) for m in self._members],
            "tasks": [asdict(t) for t in self._tasks]}
        self._data_file.parent.mkdir(parents=True, exist_ok = True  )
        with open(self._data_file, "w", encoding="utf-8") as d:
            json.dump(raw, d, indent=2)
    # LOGS
    def log(self, user, action, target_id):
        member =self.get_member(target_id)

        entry = AuditEntry(
            time = datetime.now().isoformat(timespec="seconds"),
            name = user.name,
            action = action,
            target_id =str(target_id),
            target_name = member.name
        )
        #Adds entry to the app list, then appends the csv
        self._audit.append(entry)
        self.write_audit(entry)

    # RULES 
    def can_view(self, user, member_id):
       return user.role == "MANAGER" or user.member_id == member_id
    
    def check_can_view(self, user, member_id):
        if not self.can_view(user, member_id):
            raise AccessDenied("You can only view your own workload")
    def require_manager(self, user):
        if user.role != "MANAGER":
            raise AccessDenied("Managers only")


        

    # READING
    def get_tasks(self, user, member_id):
        self.check_can_view(user, member_id)
        task_list = []
        for t in self._tasks:
            if t.assigned_id == member_id:
                task_list.append(t)
        return task_list
    
    def get_member(self, member_id):
        for m in self._members:
            if m.id == member_id:
                return m
        raise NotFound(f"No member with {member_id} found ")
    
    def get_task(self, task_id):
        for t in self._tasks:
            if t.id == task_id:
                return t
        raise NotFound(f"No task with {task_id} found ")
    
    def get_members(self, user):
        if user.role == "MANAGER":
            return list(self._members)
        return [m for m in self._members if m.id == user.member_id ]
    
    def get_audit_log(self, user):
        self.require_manager(user)
        return list(reversed(self._audit)) 
    
        #Logs when a team leader or manager views a profile

    def view_profile(self, user, member_id):
        self.check_can_view(user, member_id)
        if user.member_id != member_id:
            self.log(user, "viewed profile", member_id)
        return self.get_member(member_id)  


    # Main Function: 
    # Checks unfinished work against capacity, 
    # Loops through tasks and adds together weekly hours 
    # Measures against capacity as a percentage 

    def workload(self, user, member_id):
        member = self.get_member(member_id)
        tasks = self.get_tasks(user, member_id)
        open_hours = 0
        open_count = 0
        for t in tasks:
            
            if t.status != "done":
                open_hours = open_hours + t.est_hours
                open_count = open_count + 1

        if member.weekly_hours > 0:
            utilisation = open_hours/member.weekly_hours
        else:
            utilisation = 0
        return Workload(
            member_id=member_id,
            open_hours=open_hours,
            capacity=member.weekly_hours,
            utilisation=utilisation,
            label = status_label(utilisation),
            open_tasks = open_count,
                )
    
            

    def get_hours(self, user, task_id):
        task = self.get_task(task_id)
        self.check_can_view(user, task.assigned_id)
        return task.est_hours

    def get_capacity(self, user, member_id):
        self.check_can_view(user, member_id)
        return self.get_member(member_id).weekly_hours
    def next_task_id(self):
        return max((t.id for t in self._tasks), default = 0) + 1 
    # WRITING
    def remove_task(self, user, task_id):
        self.require_manager(user)
        task = self.get_task(task_id)
        self._tasks.remove(task)
        self._save()

        self.log(
            user,
            f"Removed task: {task.name} ID {task.id}",
            task.assigned_id    
            
        )
    def add_task(self, user, name, assigned_id, difficulty, est_hours):
        self.require_manager(user)
        self.get_member(assigned_id)
        task = Task(
            id = self.next_task_id(),
            name = name,
            difficulty = difficulty,
            est_hours= est_hours,
            assigned_id= assigned_id
        )
        
        self._tasks.append(task)
        self._save()
        self.log(
            user,
            f"Task {task.name} ID {task.id}",
            task.assigned_id
        )
        return task
    
    def reassign_task(self, user, member_id, task_id):
        self.require_manager(user)
        task = self.get_task(task_id)
        self.get_member(member_id)
        updated_task = Task(
            id=task.id,
            name=task.name,
            difficulty=task.difficulty,
            est_hours=task.est_hours,
            assigned_id=member_id,
            priority=task.priority,
            status=task.status,
            due=task.due
            )
        self._tasks = [
            updated_task if t.id == task_id else t
            for t in self._tasks
            ]
        self._save()
        self.log(
            user,
            f"Reassigned task {task.name} ID {task.id}"
            f"from employee {task.assigned_id} to employee {member_id}",
            member_id
        )
    # AUDIT (Prevent Misuse)

    def write_audit(self, entry):
        if not AUTOSAVE:
            return
        #Checks whether the file is already there 
        new_file = not self._audit_file.exists()
        with open(self._audit_file, "a" , newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[x.name for x in fields(AuditEntry)])
            if new_file:
                writer.writeheader()
            #Turns the Audit Entry into a dictionary as one line
            writer.writerow(asdict(entry))








