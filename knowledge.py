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


# --Data-- 

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
               "restrictPosting": True, "memberIds": ["E01", "E03", "E06"], "createdBy": "E01"})

#company announcements can be read by everyone but only members can post
TOPICS.append({"id": "TP8", "name": "Company Announcements", "restrictAccess": False,
               "restrictPosting": True, "memberIds": ["E01", "E02"], "createdBy": "E01"})

#example posts 
#topicId is which topic a post belongs to
#authorId is who wrote it
#solved/solution only matters for issue posts

POSTS = [
    {"id": "PO1", "topicId": "TP3", "authorId": "E14", "createdDate": db["today"],
     "kind": "How-to", "solved": False, "solution": "",
     "title": "How to order printing paper",
     "body": "Email procurement with your cost code and the paper size you need."},
    {"id": "PO2", "topicId": "TP2", "authorId": "E03", "createdDate": db["today"],
     "kind": "Issue", "solved": True,
     "solution": "Raise the session timeout in the server config.",
     "title": "Login timeout after 15 minutes",
     "body": "Users are logged out after 15 minutes of inactivity."},
    {"id": "PO3", "topicId": "TP8", "authorId": "E01", "createdDate": db["today"],
     "kind": "General", "solved": False, "solution": "",
     "title": "Welcome to the knowledge base",
     "body": "Share what you know. Anyone can start a new topic."},
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

    #checks who is logged in

    @property
    def user_id(self):
        # looked up each time so it is always the current user
        return session.get()["id"]

    def showEvent(self, event):
        #Qt calls this every time the page appears on screen.
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

        # second question
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
        a member. There is no screen to add more members yet.
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
        can_solve = (p["kind"] == "Issue" and not p["solved"]
                     and (p["authorId"] == user["id"] or user["role"] == "manager"))
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
