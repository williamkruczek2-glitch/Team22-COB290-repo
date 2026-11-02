"""
knowledge.py  (R04 / R05: topics and posts)

The knowledge base page. Staff can:
-make topics (no approval needed)
-restrict a topic so only some people can see it, or only some can post in it
-write posts in a topic (a post can be General, How-to or Issue)
-mark an Issue post as solved and optionally add a solution note

Everything is stored in plain Python lists for now. In Part 2 lists get
replaced by database tables.
"""

from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QListWidget, QLineEdit, QTextEdit, QPushButton, QComboBox, QInputDialog, QMessageBox)
import ui                         #shared page class, labels, panels, pills
import session                    #who is logged in
from styles import T              #current colour theme 
from mock_data import db          #shared fake data (employees, areas, today's date)


#data 

#look up employee by id, e.g. EMPLOYEES["E01"]["name"]
EMPLOYEES = {e["id"]: e for e in db["employees"]}

#types of posts user can pick from
KINDS = ["General", "How-to", "Issue"]


#restrictAccess - True means only members can see the topic
#restrictPosting - True means only members can post in it
#memberIds - ids of the people allowed in (used when restricted)
#createdBy - who made the topic (the creator always counts as a member)

TOPICS = [
    {"id": f"TP{i + 1}", "name": area, "restrictAccess": False,
    "restrictPosting": False, "memberIds": [], "createdBy": "E01"}
    for i, area in enumerate(db["areas"])
]

#extra topics so restrictions can be tested
#payroll portal is members only
TOPICS.append({"id": "TP7", "name": "Payroll Portal", "restrictAccess": True,
               "restrictPosting": True, "memberIds": ["E01", "E03"], "createdBy": "E01"})

#company announcements can be read by everyone but only members can post
TOPICS.append({"id": "TP8", "name": "Company Announcements", "restrictAccess": False,
               "restrictPosting": True, "memberIds": ["E01", "E02"], "createdBy": "E01"})

#only members can see e.g. without clara
TOPICS.append({"id": "TP9", "name": "Salary Reviews", "restrictAccess": True,
               "restrictPosting": True, "memberIds": ["E01"], "createdBy": "E01"})

#example posts 
#topicId is which topic a post belongs to
#authorId is who wrote it
#solved/solution only matters for issue posts

POSTS = [
    {"id": "P100", "topicId": "TP3", "authorId": "E14", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "How to order printing paper",
     "body": "Email procurement with your cost code and the paper size you need."},
    {"id": "P101", "topicId": "TP2", "authorId": "E03", "createdDate": db["today"],
     "kind": "Issue", "solved": True,
     "solution": "Raise the session timeout in the server config.",
     "title": "Login timeout after 15 minutes",
     "body": "Users are logged out after 15 minutes of inactivity."},
    {"id": "P102", "topicId": "TP8", "authorId": "E01", "createdDate": db["today"],
     "kind": "General", "solved": False, "solution": "",
     "title": "Welcome to the knowledge base",
     "body": "Share what you know. Anyone can start a new topic."},



        # ---- Software Development (TP1) ----
    {"id": "PO1", "topicId": "TP1", "authorId": "E03", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Setting up the local dev environment",
     "body": "1. Clone the repo and open it in VS Code.\n"
             "2. Create a virtual environment: python3 -m venv .venv\n"
             "3. Install the requirements with pip install -r requirements.txt\n"
             "4. Run main.py and check the app opens.\n\n"
             "If the Qt window fails to start, reinstall PySide6 first."},
    {"id": "PO2", "topicId": "TP1", "authorId": "E04", "createdDate": db["today"],
     "kind": "General", "solved": False, "solution": "",
     "title": "Code review checklist we agreed on",
     "body": "Before asking for a review: the app runs, names are clear, and there "
             "are no leftover debug prints. Reviewers should reply within one working day."},
    {"id": "PO3", "topicId": "TP1", "authorId": "E06", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Writing a good commit message",
     "body": "Start with a short summary of what changed, in the present tense. Make "
             "small, frequent commits so everyone's work shows up in the history."},
    {"id": "PO4", "topicId": "TP1", "authorId": "E05", "createdDate": db["today"],
     "kind": "Issue", "solved": True,
     "solution": "Run the tests from the project root, not from inside the tests folder.",
     "title": "Unit tests fail with import errors",
     "body": "The tests pass on one machine but fail on another with module not "
             "found errors."},

    # ---- Software Issues (TP2) ----
    {"id": "PO6", "topicId": "TP2", "authorId": "E05", "createdDate": db["today"],
     "kind": "Issue", "solved": False, "solution": "",
     "title": "CSV export drops the last row",
     "body": "The helpdesk export is missing the final ticket every time. It looks "
             "like an off-by-one in the loop."},
    {"id": "PO7", "topicId": "TP2", "authorId": "E07", "createdDate": db["today"],
     "kind": "Issue", "solved": False, "solution": "",
     "title": "Email parser fails on attachments with spaces in the name",
     "body": "Tickets created from emails are skipped when the attachment filename "
             "contains a space. No error is shown to the sender."},
    {"id": "PO8", "topicId": "TP2", "authorId": "E04", "createdDate": db["today"],
     "kind": "Issue", "solved": True,
     "solution": "Clear the browser cache and reload; the old script was being served.",
     "title": "Dashboard shows old data after an update",
     "body": "Some users still see last week's numbers after the new version went out."},

    # ---- Printing (TP3) ----
    {"id": "PO10", "topicId": "TP3", "authorId": "E08", "createdDate": db["today"],
     "kind": "Issue", "solved": True,
     "solution": "Reinstall the driver from the managed print server, not the vendor site.",
     "title": "New printers show as offline on some laptops",
     "body": "A few laptops list the new floor printers as offline even though "
             "they print fine from other machines."},
    {"id": "PO11", "topicId": "TP3", "authorId": "E09", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Using secure print release",
     "body": "Send your job as normal, then tap your badge on the printer and pick the "
             "job from the list. Anything not released is deleted overnight."},
    {"id": "PO12", "topicId": "TP3", "authorId": "E16", "createdDate": db["today"],
     "kind": "Issue", "solved": False, "solution": "",
     "title": "Duplex printing defaults to single sided",
     "body": "Jobs from the admin floor come out single sided even though duplex "
             "should be the default. It might be a queue setting."},

    # ---- Networking (TP4) ----
    {"id": "PO13", "topicId": "TP4", "authorId": "E10", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Checking a switch port is on the right VLAN",
     "body": "1. Log in to the switch.\n"
             "2. Run the port status command for the port you are checking.\n"
             "3. Confirm the VLAN matches the floor plan.\n"
             "4. If not, change it and write the change in the network log."},
    {"id": "PO14", "topicId": "TP4", "authorId": "E11", "createdDate": db["today"],
     "kind": "Issue", "solved": False, "solution": "",
     "title": "Slow wifi on the second floor after the switch swap",
     "body": "Speeds drop in the afternoon. Might be the new access point channel "
             "overlapping with the one next door."},
    {"id": "PO15", "topicId": "TP4", "authorId": "E12", "createdDate": db["today"],
     "kind": "Issue", "solved": True,
     "solution": "Replace the patch cable; the old one had a damaged connector.",
     "title": "Desk port keeps dropping the connection",
     "body": "One desk on the first floor loses its wired connection every few minutes."},
    {"id": "PO16", "topicId": "TP4", "authorId": "E11", "createdDate": db["today"],
     "kind": "General", "solved": False, "solution": "",
     "title": "Switch firmware patching window",
     "body": "Firmware updates happen on the first Saturday of each month. Anything "
             "that cannot tolerate a short outage should be flagged the week before."},

    # ---- Hardware (TP5) ----
    {"id": "PO17", "topicId": "TP5", "authorId": "E09", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Asset-tagging new equipment",
     "body": "Every new device gets a tag before it leaves the store room. Log the "
             "tag number, serial number and who it was issued to in the asset sheet."},
    {"id": "PO18", "topicId": "TP5", "authorId": "E08", "createdDate": db["today"],
     "kind": "Issue", "solved": False, "solution": "",
     "title": "Docking station not charging some laptops",
     "body": "It works for most models but not the older ones. Might need a higher "
             "wattage adapter."},
    {"id": "PO19", "topicId": "TP5", "authorId": "E12", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Disposing of old equipment",
     "body": "Wipe the drive, remove the asset tag from the live list and hand the "
             "device to the store room for collection. Never put it in general waste."},

    # ---- Admin & Procurement (TP6) ----
    {"id": "PO20", "topicId": "TP6", "authorId": "E15", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Raising a purchase order",
     "body": "1. Get a quote from the supplier.\n"
             "2. Fill in the purchase order form with the project code.\n"
             "3. Send it to your manager for sign-off.\n"
             "4. Once approved, procurement places the order."},
    {"id": "PO21", "topicId": "TP6", "authorId": "E16", "createdDate": db["today"],
     "kind": "General", "solved": False, "solution": "",
     "title": "New starter checklist is now one page",
     "body": "The onboarding pack now has a single checklist covering desk, accounts "
             "and kit. Ask Ruth if you need a copy for a new starter."},
    {"id": "PO22", "topicId": "TP6", "authorId": "E17", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Booking the training room",
     "body": "Check the room calendar first, then email the office team with the date, "
             "time and number of people. Say if you need a projector."},

    # ---- Payroll Portal (TP7, members only: E01, E03, E06) ----
    {"id": "PO23", "topicId": "TP7", "authorId": "E06", "createdDate": db["today"],
     "kind": "Issue", "solved": False, "solution": "",
     "title": "Legacy login still reachable by direct link",
     "body": "The old login page still loads if you go to it directly. It needs to "
             "be switched off before the upgrade goes live."},
    {"id": "PO24", "topicId": "TP7", "authorId": "E03", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Testing the new payslip page",
     "body": "Use the test account, open the payslip page and check the totals match "
             "the sample data. Report anything that looks off in this topic."},

    # ---- Company Announcements (TP8, only E01 and E02 can post) ----
    {"id": "PO25", "topicId": "TP8", "authorId": "E01", "createdDate": db["today"],
     "kind": "General", "solved": False, "solution": "",
     "title": "Tips for getting the most out of the knowledge base",
     "body": "You can restrict who sees a topic or who posts in it. Mark issues as "
             "solved with the fix so the next person can find it."},
    {"id": "PO26", "topicId": "TP8", "authorId": "E02", "createdDate": db["today"],
     "kind": "General", "solved": False, "solution": "",
     "title": "Network maintenance this weekend",
     "body": "The second floor switches are being replaced on Saturday morning. "
             "Expect short outages. Please save your work on Friday."},

    # ---- Salary Reviews (TP9, members only: E01, E02, E13) ----
    {"id": "PO27", "topicId": "TP9", "authorId": "E01", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "Preparing for a salary review meeting",
     "body": "1. Collect the team's objectives and how each person met them.\n"
             "2. Note any extra responsibilities taken on this year.\n"
             "3. Check the pay band for the role.\n"
             "4. Book 30 minutes and share the agenda a few days ahead."},
    {"id": "PO28", "topicId": "TP9", "authorId": "E13", "createdDate": db["today"],
     "kind": "General", "solved": False, "solution": "",
     "title": "Review window opens next month",
     "body": "HR needs all review forms back before the window closes. Managers should "
             "keep their notes in the shared review folder, not in email."},
    {"id": "PO29", "topicId": "TP9", "authorId": "E02", "createdDate": db["today"],
     "kind": "Issue", "solved": False, "solution": "",
     "title": "Review form will not save on the second page",
     "body": "The form loses what was typed on page two when you go back. Using the "
             "browser back button seems to make it worse."},
    {"id": "PO30", "topicId": "TP9", "authorId": "E13", "createdDate": db["today"],
     "kind": "Issue", "solved": True,
     "solution": "Use the Save draft button before moving between pages.",
     "title": "Draft reviews disappearing",
     "body": "Two managers lost half-written reviews when their session timed out."},
]


#access rules 

def is_member(topic, user_id):
    #a member is someone on the member list or the person who made the topic
    return user_id in topic["memberIds"] or user_id == topic["createdBy"]


def can_see(topic, user_id):
    #open topics visible to everyone if access is restricted only members can see it
    if not topic["restrictAccess"]:
        return True
    return is_member(topic, user_id)


def can_post(topic, user_id):
    #can't post in something you can't see
    if not can_see(topic, user_id):
        return False
    #if posting is restricted, you need to be a member
    if topic["restrictPosting"]:
        return is_member(topic, user_id)
    return True


def topic_label(topic):
    #the text shown in the topic list, with a note if the topic is restricted
    if topic["restrictAccess"]:
        return topic["name"] + "  (members only)"
    if topic["restrictPosting"]:
        return topic["name"] + "  (read-only)"
    return topic["name"]


#pills

def topic_pill(topic):
    if topic["restrictAccess"]:
        return ui.pill("warning", "!", "Members only")
    if topic["restrictPosting"]:
        return ui.pill("warning", "!", "Read-only for non-members")
    return ui.pill("good", "✓", "Open to everyone")


def nice_date(d):
    #formats date
    try:
        return ui.fmtDate(d)
    except Exception:
        return str(d)


def fill_row(layout, *widgets):
    # Empty a row of pills, then put the given widgets in it
    ui.clear(layout)
    for w in widgets:
        layout.addWidget(w)
    layout.addStretch()


def local_style():
    #knowledge page has a few extra style tweaks on top of the global theme 
    #list + text boxes and buttons
    v = T
    return f"""

QListWidget, QTextEdit, QLineEdit {{
    background: {v['surface']}; color: {v['ink']};
    border: 1px solid {v['rule']}; border-radius: 6px; padding: 6px;}}

QListWidget::item {{padding: 7px 8px; border-radius: 4px;}}

QListWidget::item:selected {{
    background: {v['surface-2']}; color: {v['ink']};
    border-left: 3px solid {v['accent']};}}

QPushButton {{
    background: {v['surface-2']}; color: {v['ink']};
    border: 1px solid {v['rule']}; border-radius: 6px; padding: 8px 14px;}}

QPushButton:hover {{ border-color: {v['accent']}; }}

QPushButton[class="primary"] {{
    background: {v['accent']}; color: {v['page']}; border: none; font-weight: bold;}}

"""


#the page itself

class KnowledgePage(ui.Page):
    def __init__(self):
        #ui.Page sets up self.main, the layout for the page content
        super().__init__()
        self.setStyleSheet(local_style())

        #topics the current user is allowed to see
        self.topics = []
        #posts for whichever topic is selected right now
        self.visible_posts = []

        #page heading
        self.main.addWidget(ui.label("Knowledge base", "h1"))
        self.main.addWidget(ui.label(
            "Share what you know with the rest of the company. Pick a topic to "
            "read its posts, or start a new one.", "lede"))

        #topics on the left, posts on the right
        row = QHBoxLayout()
        row.setSpacing(16)

        #left panel: the list of topics
        topics_panel, topics_lay = ui.panel()
        topics_lay.addWidget(ui.label("Topics", "h2"))

        self.topic_list = QListWidget()
        self.topic_list.setMinimumHeight(380)
        #when a different topic is clicked, show that topic's posts
        self.topic_list.currentRowChanged.connect(self.show_posts)
        topics_lay.addWidget(self.topic_list)

        new_topic_btn = QPushButton("New topic")
        new_topic_btn.setProperty("class", "primary")
        new_topic_btn.clicked.connect(self.add_topic)
        topics_lay.addWidget(new_topic_btn)

        #right side: two panels, one for reading and one for writing
        right = QVBoxLayout()
        right.setSpacing(16)

        #reading panel
        posts_panel, posts_lay = ui.panel()
        posts_lay.addWidget(ui.label("Posts", "h2"))

        #row of pills showing open status of the chosen topic 
        self.topic_info = QHBoxLayout()
        posts_lay.addLayout(self.topic_info)

        self.post_list = QListWidget()
        self.post_list.setMinimumHeight(130)
        #when a post is clicked, show its full text underneath
        self.post_list.currentRowChanged.connect(self.show_body)
        posts_lay.addWidget(self.post_list)

        #row of pills for the chosen post (solved or open issue)
        self.post_info = QHBoxLayout()
        posts_lay.addLayout(self.post_info)

        #read-only box that shows the selected post
        self.reader = QTextEdit()
        self.reader.setReadOnly(True)
        self.reader.setMinimumHeight(170)
        posts_lay.addWidget(self.reader)

        #only shown when the selected post is an unsolved Issue the user can close
        self.solve_btn = QPushButton("Mark as solved")
        self.solve_btn.clicked.connect(self.mark_solved)
        self.solve_btn.setVisible(False)
        posts_lay.addWidget(self.solve_btn)

        #writing panel: the form for a new post
        form_panel, form_lay = ui.panel()
        form_lay.addWidget(ui.label("Create a post", "h2"))

        self.kind_in = QComboBox()
        self.kind_in.addItems(KINDS)
        #show the solution box only when the kind is Issue
        self.kind_in.currentTextChanged.connect(self.on_kind_change)
        form_lay.addWidget(self.kind_in)

        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Post title")
        form_lay.addWidget(self.title_in)

        self.body_in = QTextEdit()
        self.body_in.setPlaceholderText("Write anything that helps. There is no fixed format.")
        self.body_in.setMinimumHeight(110)
        form_lay.addWidget(self.body_in)

        self.solution_in = QLineEdit()
        self.solution_in.setPlaceholderText("Solution (optional, for issues)")
        self.solution_in.setVisible(False)    
        form_lay.addWidget(self.solution_in)

        post_btn = QPushButton("Post")
        post_btn.setProperty("class", "primary")
        post_btn.clicked.connect(self.add_post)
        form_lay.addWidget(post_btn)

        right.addWidget(posts_panel)
        right.addWidget(form_panel)

        #right side gets twice the width
        row.addWidget(topics_panel, 1)
        row.addLayout(right, 2)
        self.main.addLayout(row)

        #formatting to keep everything at the top if the window is tall
        self.finish()

    #checks who is logged in, more applicable in part 2

    @property
    def user_id(self):
        #looked up each time so it is always the current user
        return session.get()["id"]

    def showEvent(self, event):
        #Qt calls this every time the page appears on screen
        #topic list is rebuilt here in case the logged in user changed
        super().showEvent(event)
        topic = self.current_topic()
        self.refresh_topics(select_id=topic["id"] if topic else None)

    #topics

    def refresh_topics(self, select_id=None):
        #rebuild the topic list so only has topics user can see
        self.topics = [t for t in TOPICS if can_see(t, self.user_id)]

        self.topic_list.blockSignals(True) #stops the list firing "row changed" while it is being cleared and refilled
        self.topic_list.clear()
        for t in self.topics:
            self.topic_list.addItem(topic_label(t))
        self.topic_list.blockSignals(False)

        #works out which row to select: the one asked for otherwise the first
        row = 0
        if select_id:
            for i, t in enumerate(self.topics):
                if t["id"] == select_id:
                    row = i
        if self.topics:
            self.topic_list.setCurrentRow(row)
            self.show_posts(row)
        else:
            self.show_posts(-1) #nothing to show

    def add_topic(self):
        #anyone can make a topic, no approval needed (client requirement)
        name, ok = QInputDialog.getText(self, "New topic", "Topic name:")
        name = name.strip()
        if not ok or name == "":
            return

        #don't allow two topics with the same name 
        for t in TOPICS:
            if t["name"].lower() == name.lower():
                QMessageBox.information(self, "Topic exists",
                                        "A topic with that name already exists.")
                return

        #first question
        answer = QMessageBox.question(
            self, "Restrict access?",
            "Only chosen people can see this topic?\n(No = everyone can read it.)")
        restrict_access = (answer == QMessageBox.Yes)

        #second question
        if restrict_access:
            restrict_posting = True
        else:
            answer = QMessageBox.question(
                self, "Restrict posting?",
                "Only chosen people can post in this topic?\n"
                "(No = everyone who can see it can post.)")
            restrict_posting = (answer == QMessageBox.Yes)

        """
        For the prototype a restricted topic starts with only its creator as
        a member. There is no screen to add more members yet. Is currenly hardcoded.
        """

        members = []
        if restrict_access or restrict_posting:
            members = [self.user_id]

        topic = {"id": f"TP{len(TOPICS) + 1}", "name": name,
                 "restrictAccess": restrict_access,
                 "restrictPosting": restrict_posting,
                 "memberIds": members, "createdBy": self.user_id}
        TOPICS.append(topic)

        #redraw the list and select the new topic
        self.refresh_topics(select_id=topic["id"])

    #posts

    def current_topic(self):
        #the topic currently highlighted in the list
        row = self.topic_list.currentRow()
        if 0 <= row < len(self.topics):
            return self.topics[row]
        return None

    def show_posts(self, row):
        #clear everything first then fill the post list for the chosen topic
        self.post_list.clear()
        self.reader.clear()
        self.solve_btn.setVisible(False)
        fill_row(self.post_info)
        self.visible_posts = []

        topic = self.current_topic()
        if topic is None:
            fill_row(self.topic_info)
            return

        fill_row(self.topic_info, topic_pill(topic))

        self.visible_posts = [p for p in POSTS if p["topicId"] == topic["id"]]
        for p in self.visible_posts:
            label = p["kind"]
            if p["solved"]:
                label += ", solved"
            self.post_list.addItem(f"[{label}] {p['title']}")

    def show_body(self, row):
        #show the full text of clicked post in reading box
        self.solve_btn.setVisible(False)
        fill_row(self.post_info)
        if row < 0 or row >= len(self.visible_posts):
            self.reader.clear()
            return

        p = self.visible_posts[row]
        author = EMPLOYEES[p["authorId"]]["name"]
        text = (f"{p['title']}\n{p['kind']} by {author} on "
                f"{nice_date(p['createdDate'])}\n\n{p['body']}")
        if p["solved"] and p["solution"]:
            text += f"\n\nSolution: {p['solution']}"
        self.reader.setPlainText(text)

        #issue posts get a pill which shows if they are solved
        if p["kind"] == "Issue":
            if p["solved"]:
                fill_row(self.post_info, ui.pill("good", "✓", "Solved"))
            else:
                fill_row(self.post_info, ui.pill("warning", "!", "Open issue"))

        #mark as solved button is only for unsolved Issue posts and only
        #the author or a manager can use it
        user = session.get()
        can_solve = (p["kind"] == "Issue" and not p["solved"] and
                     (p["authorId"] == user["id"] or user["role"] == "manager"))
        self.solve_btn.setVisible(can_solve)

    def mark_solved(self):
        row = self.post_list.currentRow()
        if row < 0 or row >= len(self.visible_posts):
            return

        #ask what fixed it. user can leave this empty and just mark it solved
        solution, ok = QInputDialog.getMultiLineText(
            self, "Mark as solved", "What fixed it? (optional)")
        if not ok:
            return  #if cancel change nothing

        post = self.visible_posts[row]
        post["solved"] = True
        post["solution"] = solution.strip()

        #redraw list so "solved" label appears then keep the same post selected
        self.show_posts(self.topic_list.currentRow())
        self.post_list.setCurrentRow(row)

    def on_kind_change(self, kind):
        #solution box only for issue posts
        self.solution_in.setVisible(kind == "Issue")

    def add_post(self):
        topic = self.current_topic()
        title = self.title_in.text().strip()
        body = self.body_in.toPlainText().strip()

        #need a topic, a title and some text
        if topic is None or title == "" or body == "":
            return

        #check if the user is allowed to post here (for read-only topics)
        if not can_post(topic, self.user_id):
            QMessageBox.information(self, "Read-only topic", "Only chosen members can post in this topic.")
            return

        kind = self.kind_in.currentText()
        solution = ""
        if kind == "Issue":
            solution = self.solution_in.text().strip()

        #issue that already has a solution is saved as solved
        POSTS.append({"id": f"PO{len(POSTS) + 1}", "topicId": topic["id"],
                      "authorId": self.user_id, "createdDate": db["today"],
                      "kind": kind, "solved": solution != "", "solution": solution,
                      "title": title, "body": body})

        #clear the form and refresh the posts list so the new post shows up
        self.title_in.clear()
        self.body_in.clear()
        self.solution_in.clear()
        self.show_posts(self.topic_list.currentRow())
