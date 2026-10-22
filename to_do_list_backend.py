from datetime import date
import uuid # randomised IDs with 2^122 unique combinations
import json

# this dictionary holds all the fields required for the to do items
to_do_item = {
    "projectId": None, # in uuid format and used for to do list operations (e.g. sorting)
    "title": None,
    "dueDate": None, # in python built-in date format
    "status": None,
    "assigneeId": None
}
    

def add_item(title, dueDate, assigneeId):    
    # checks if the dueDate is input in a date format
    try:
        # converts dueDate from string to date
        date.fromisoformat(dueDate)
        # assigns the parameters to the dictionary
        to_do_item["dueDate"] = dueDate
        to_do_item["title"] = title    
        to_do_item["projectId"] = str(uuid.uuid4()) # generates random uuid
        to_do_item["status"] = "todo"
        to_do_item["assigneeId"] = assigneeId
        try:
            # reads a flat json file
            with open("to_do_list.json", "r") as f:
                # stores read data in a variable
                data = json.load(f)
            # adds the new item to the list of currently stored items
            data.append(to_do_item)
            # writes the appended data back to the file
            with open("to_do_list.json", "w") as f:
                json.dump(data, f, indent=4) # indent=4 lays out the json so that it is more readable (multiple lines + 4-space indents)
        except FileNotFoundError:
            data = []
            with open("to_do_list.json", "w") as f:
                json.dump(data, f, indent=4)
    except ValueError:
        print("Date was invalid")
        temporaryCLI()
    

# removes to do items based on id
def remove_item(projectId):
    with open("to_do_list.json", "r") as f:
        data = json.load(f)
    # iterates through data to find the item to remove
    for item in data:
        # checks if the current item is the item to be removed
        if item["projectId"] == projectId:
            # removes the item from data
            data.remove(item)
    with open("to_do_list.json", "w") as f:
        json.dump(data, f, indent=4)

# returns a list of all items
def view_items():
    with open("to_do_list.json", "r") as f:
        data = json.load(f)
    return data


# temporary user interface implemented using a CLI approach which later be superseeded by the main frontend
def temporaryCLI():
    # menu screen
    print("Welcome to the to do list interface.")
    print("(1) View all items")
    print("(2) Add an item")
    print("(3) Remove an item")
    option = input("Enter your choice: ")

    if option == "1":
        # prints the list of items
        for toDoItem in view_items():
            print("Title: "+toDoItem.get("title")+" | Due: "+toDoItem.get("dueDate"))

    elif option == "2":
        # retrieves to do item data from the user and add it to the file
        title = input("Enter the title of the item: ")
        dueDate = input("Enter the due date (in the form yyyy-mm-dd) of the item: ")
        assigneeId = input("Enter the assigneeId of the item: ")
        add_item(title, dueDate, assigneeId)

    elif option == "3":
        # retrieves id from the user and removes it from the file
        projectId = input("Enter the id of the item you want to remove: ")
        remove_item(projectId)

    else:
        temporaryCLI()

#temporaryCLI()
