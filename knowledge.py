"""
knowledge.py  (R04 / R05: topics and posts)

The knowledge base page. Staff can:
  - make topics (no approval needed)
  - restrict a topic so only some people can see it, or only some can post in it
  - write posts in a topic (a post can be General, How-to or Issue)
  - mark an Issue post as solved

Everything is stored in lists for now.
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLineEdit, QTextEdit, QPushButton, QLabel, QInputDialog, QComboBox, QMessageBox)
import ui                         
import session                    
from mock_data import db          

# --- Data ---

# Look up an employee by id, e.g. EMPLOYEES["E01"]["name"]
EMPLOYEES = {e["id"]: e for e in db["employees"]}

# The types of post a user can pick from
KINDS = ["General", "How-to", "Issue"]

# Start with one topic for each skill area in mock_data.py. Using the same names
# as areas lets the Insights training chart link to these topics later.
# Fields on each topic:
#   restrictAccess  - True means only members can see the topic
#   restrictPosting - True means only members can post in it
#   memberIds       - ids of the people allowed in (used when restricted)
#   createdBy       - who made the topic (the creator always counts as a member)
TOPICS = [
    {"id": f"TP{i + 1}", "name": area, "restrictAccess": False,
     "restrictPosting": False, "memberIds": [], "createdBy": "E01"}
    for i, area in enumerate(db["areas"])
]

# Two extra topics so the restrictions can be tested.
# Payroll Portal is members only.
TOPICS.append({"id": "TP7", "name": "Payroll Portal", "restrictAccess": True,
               "restrictPosting": True, "memberIds": ["E01", "E03", "E06"],
               "createdBy": "E01"})
# Company Announcements can be read by everyone, but only members can post.
TOPICS.append({"id": "TP8", "name": "Company Announcements", "restrictAccess": False,
               "restrictPosting": True, "memberIds": ["E01", "E02"],
               "createdBy": "E01"})

# example posts. topicId says which topic a post belongs to, and
# authorId says who wrote it.
# solved/solution only matter for issue posts.
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


# ---Access rules---


def is_member(topic, user_id):
    # A member is someone on the member list, or the person who made the topic
    return user_id in topic["memberIds"] or user_id == topic["createdBy"]


def can_see(topic, user_id):
    # Open topics are visible to everyone. If access is restricted,
    # only members can see it.
    if not topic["restrictAccess"]:
        return True
    return is_member(topic, user_id)


def can_post(topic, user_id):
    # You can't post in something you can't see
    if not can_see(topic, user_id):
        return False
    # If posting is restricted, you also need to be a member
    if topic["restrictPosting"]:
        return is_member(topic, user_id)
    return True


def topic_label(topic):
    # The text shown in the topic list, with a note if the topic is restricted
    if topic["restrictAccess"]:
        return topic["name"] + "  (members only)"
    if topic["restrictPosting"]:
        return topic["name"] + "  (read-only)"
    return topic["name"]


# --- Knowledge Page ---

class KnowledgePage(ui.Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # topics the current user is allowed to see (filled in by refresh_topics)
        self.topics = []
        # posts for whichever topic is selected right now
        self.visible_posts = []

        # Everything goes inside one container widget, which is added to the
        # page at the bottom of this method
        content = QWidget()
        root = QHBoxLayout(content)       # topics on the left, posts on the right

        # ---- left side: the list of topics ----
        left = QVBoxLayout()
        left.addWidget(QLabel("Topics"))

        self.topic_list = QListWidget()
        # when a different topic is clicked, show that topic's posts
        self.topic_list.currentRowChanged.connect(self.show_posts)

        new_topic_btn = QPushButton("New topic")
        new_topic_btn.clicked.connect(self.add_topic)

        left.addWidget(self.topic_list)
        left.addWidget(new_topic_btn)

        # ---- right side: posts, reading area and the new post form ----
        right = QVBoxLayout()
        right.addWidget(QLabel("Posts"))

        self.post_list = QListWidget()
        # when a post is clicked, show its full text underneath
        self.post_list.currentRowChanged.connect(self.show_body)

        # read-only box that shows the selected post
        self.reader = QTextEdit()
        self.reader.setReadOnly(True)

        # only shown when the selected post is an unsolved Issue the user can close
        self.solve_btn = QPushButton("Mark as solved")
        self.solve_btn.clicked.connect(self.mark_solved)
        self.solve_btn.setVisible(False)

        # the form for writing a new post
        self.kind_in = QComboBox()
        self.kind_in.addItems(KINDS)
        # show the solution box only when the kind is Issue
        self.kind_in.currentTextChanged.connect(self.on_kind_change)

        self.title_in = QLineEdit()
        self.title_in.setPlaceholderText("Post title")

        self.body_in = QTextEdit()
        self.body_in.setPlaceholderText("Write anything that helps. There is no fixed format.")

        self.solution_in = QLineEdit()
        self.solution_in.setPlaceholderText("Solution (optional, for issues)")
        self.solution_in.setVisible(False)    # hidden until Issue is picked

        post_btn = QPushButton("Post")
        post_btn.clicked.connect(self.add_post)

        # the numbers are stretch factors: bigger = takes more of the space
        right.addWidget(self.post_list, 1)
        right.addWidget(self.reader, 2)
        right.addWidget(self.solve_btn)
        right.addWidget(QLabel("Create a post"))
        right.addWidget(self.kind_in)
        right.addWidget(self.title_in)
        right.addWidget(self.body_in, 1)
        right.addWidget(self.solution_in)
        right.addWidget(post_btn)

        # put both sides side by side (right side gets twice the width)
        root.addLayout(left, 1)
        root.addLayout(right, 2)

        # add everything to the page, same way insights.py does it
        self.main.addWidget(content)

    # ---- who is logged in ----

    @property
    def user_id(self):
        # looked up each time so it is always the current user
        return session.get()["id"]

    def showEvent(self, event):
        # Qt calls this every time the page appears on screen.
        # The topic list is rebuilt here in case the logged in user changed
        # since last time, because each user can see different topics.
        super().showEvent(event)
        topic = self.current_topic()
        self.refresh_topics(select_id=topic["id"] if topic else None)

    # ---- topics ----

    def refresh_topics(self, select_id=None):
        # Rebuild the topic list so it only has topics this user can see
        self.topics = [t for t in TOPICS if can_see(t, self.user_id)]

        # blockSignals stops the list firing "row changed" while it is being
        # cleared and refilled
        self.topic_list.blockSignals(True)
        self.topic_list.clear()
        for t in self.topics:
            self.topic_list.addItem(topic_label(t))
        self.topic_list.blockSignals(False)

        # work out which row to select: the one asked for, otherwise the first
        row = 0
        if select_id:
            for i, t in enumerate(self.topics):
                if t["id"] == select_id:
                    row = i
        if self.topics:
            self.topic_list.setCurrentRow(row)
            self.show_posts(row)
        else:
            self.show_posts(-1)      # nothing to show

    def add_topic(self):
        # Anyone can make a topic, no approval needed (client requirement)
        name, ok = QInputDialog.getText(self, "New topic", "Topic name:")
        name = name.strip()
        if not ok or name == "":
            return

        # don't allow two topics with the same name (ignoring capitals)
        for t in TOPICS:
            if t["name"].lower() == name.lower():
                QMessageBox.information(self, "Topic exists",
                                        "A topic with that name already exists.")
                return

        # first question: should only some people be able to see it?
        answer = QMessageBox.question(
            self, "Restrict access?",
            "Only chosen people can see this topic?\n(No = everyone can read it.)")
        restrict_access = (answer == QMessageBox.Yes)

        # second question: should only some people be able to post?
        # If access is already restricted then posting is restricted too,
        # so there is no need to ask.
        if restrict_access:
            restrict_posting = True
        else:
            answer = QMessageBox.question(
                self, "Restrict posting?",
                "Only chosen people can post in this topic?\n"
                "(No = everyone who can see it can post.)")
            restrict_posting = (answer == QMessageBox.Yes)

        # For the prototype a restricted topic starts with only its creator as
        # a member. There is no screen to add more members yet.
        members = []
        if restrict_access or restrict_posting:
            members = [self.user_id]

        topic = {"id": f"TP{len(TOPICS) + 1}", "name": name,
                 "restrictAccess": restrict_access,
                 "restrictPosting": restrict_posting,
                 "memberIds": members, "createdBy": self.user_id}
        TOPICS.append(topic)

        # redraw the list and select the new topic
        self.refresh_topics(select_id=topic["id"])

    # ---- posts ----

    def current_topic(self):
        # the topic currently highlighted in the list, or None if nothing is selected
        row = self.topic_list.currentRow()
        if 0 <= row < len(self.topics):
            return self.topics[row]
        return None

    def show_posts(self, row):
        # clear everything first, then fill the post list for the chosen topic
        self.post_list.clear()
        self.reader.clear()
        self.solve_btn.setVisible(False)
        self.visible_posts = []

        topic = self.current_topic()
        if topic is None:
            return

        self.visible_posts = [p for p in POSTS if p["topicId"] == topic["id"]]
        for p in self.visible_posts:
            label = p["kind"]
            if p["solved"]:
                label += ", solved"
            self.post_list.addItem(f"[{label}] {p['title']}")

    def show_body(self, row):
        # show the full text of the clicked post in the reading box
        self.solve_btn.setVisible(False)
        if row < 0 or row >= len(self.visible_posts):
            self.reader.clear()
            return

        p = self.visible_posts[row]
        author = EMPLOYEES[p["authorId"]]["name"]
        text = f"{p['title']}\n{p['kind']} by {author} on {p['createdDate']}\n\n{p['body']}"

        if p["solved"] and p["solution"]:
            text += f"\n\nSolved: {p['solution']}"
        elif p["solved"]:
            text += "\n\nSolved"
        self.reader.setPlainText(text)

        # The Mark as solved button is only for unsolved Issue posts, and only
        # the author or a manager can use it.
        user = session.get()
        can_solve = (p["kind"] == "Issue" and not p["solved"]
                     and (p["authorId"] == user["id"] or user["role"] == "manager"))
        self.solve_btn.setVisible(can_solve)

    def mark_solved(self):
        row = self.post_list.currentRow()
        if row < 0 or row >= len(self.visible_posts):
            return
        self.visible_posts[row]["solved"] = True

        # redraw the list so the "solved" label appears, then keep the same post selected
        self.show_posts(self.topic_list.currentRow())
        self.post_list.setCurrentRow(row)

    def on_kind_change(self, kind):
        # the solution box only makes sense for Issue posts
        self.solution_in.setVisible(kind == "Issue")

    def add_post(self):
        topic = self.current_topic()
        title = self.title_in.text().strip()
        body = self.body_in.toPlainText().strip()

        # need a topic, a title and some text
        if topic is None or title == "" or body == "":
            return

        # check the user is allowed to post here (for read-only topics)
        if not can_post(topic, self.user_id):
            QMessageBox.information(self, "Read-only topic",
                                    "Only chosen members can post in this topic.")
            return

        kind = self.kind_in.currentText()
        solution = ""
        if kind == "Issue":
            solution = self.solution_in.text().strip()

        # an Issue that already has a solution is saved as solved
        POSTS.append({"id": f"PO{len(POSTS) + 1}", "topicId": topic["id"],
                      "authorId": self.user_id, "createdDate": db["today"],
                      "kind": kind, "solved": solution != "", "solution": solution,
                      "title": title, "body": body})

        # clear the form and refresh the posts list so the new post shows up
        self.title_in.clear()
        self.body_in.clear()
        self.solution_in.clear()
        self.show_posts(self.topic_list.currentRow())