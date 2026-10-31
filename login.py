"""
login.py - R06/R07: the sign-in and registration window, shown before the main app.

auth.py does the R06/R07 checks (email format, staff domain, password rules).
accounts.py (R08) stores accounts, sends the verification code and signs people in.
This file is only the screens.

main.py shows LoginWindow first. On a successful sign-in it calls on_success(user),
which stores the user with session.set(user) and opens the main window.
"""
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox

import accounts
import auth
import ui
from styles import T


def _style():
    v = T
    return f"""
#loginPage {{ background: {v['page']}; }}
QFrame#card {{ background: {v['surface']}; border: 1px solid {v['rule']}; border-radius: 8px; }}
QFrame#card QLabel, QFrame#card QCheckBox {{ background: transparent; border: none; }}
QFrame#card QLabel[class="fieldLabel"] {{ font-weight: bold; }}
QFrame#card QLabel[class="fieldError"] {{ color: {v['critical']}; }}
QFrame#card QLabel[class="formError"] {{ background: {v['surface-2']}; border: 1px solid {v['rule']};
    border-left: 3px solid {v['critical']}; border-radius: 6px; padding: 8px 10px; }}
QFrame#card QLabel[class="rule"] {{ color: {v['muted']}; }}
QFrame#card QLabel[class="rule ruleMet"] {{ color: {v['good']}; }}
QLabel[class="banner"] {{ background: #fff6db; color: #7a5600; border-radius: 6px; padding: 6px 10px; }}
QLabel#bigIcon {{ font-size: 28pt; color: {v['good']}; }}
QLineEdit {{ background: {v['surface']}; color: {v['ink']}; border: 1px solid {v['rule']};
    border-radius: 6px; padding: 8px 10px; }}
QLineEdit:focus {{ border: 1px solid {v['accent']}; }}
QLineEdit[invalid="true"] {{ border: 1px solid {v['critical']}; }}
QPushButton[class="primary"] {{ background: {v['accent']}; color: #ffffff; border: none;
    border-radius: 6px; padding: 10px; font-weight: bold; }}
QPushButton[class="primary"]:hover {{ background: #174a88; }}
"""


def _field(lay, text, password=False):
    lay.addWidget(ui.label(text, 'fieldLabel'))
    box = QLineEdit()
    if password:
        box.setEchoMode(QLineEdit.Password)
    lay.addWidget(box)
    return box


def _error(lay, cls='fieldError'):
    err = ui.label('', cls)
    err.hide()
    lay.addWidget(err)
    return err


def _show(err, text):
    err.setText(text)
    err.setVisible(bool(text))


def _markInvalid(box, invalid):
    box.setProperty('invalid', invalid)
    box.style().unpolish(box)
    box.style().polish(box)


def _button(text, cls, onClick):
    b = QPushButton(text)
    b.setProperty('class', cls)
    b.setCursor(Qt.PointingHandCursor)
    b.clicked.connect(onClick)
    return b


def _view():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    return w, lay


class SignInView(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(ui.label('Sign in', 'h1'))
        lay.addWidget(ui.label('Use your staff email address and password.', 'lede'))
        lay.addSpacing(8)
        self.error = _error(lay, 'formError')
        self.email = _field(lay, 'Staff email address')
        self.password = _field(lay, 'Password', password=True)
        self.password.returnPressed.connect(self.submit)
        lay.addSpacing(10)
        lay.addWidget(_button('Sign in', 'primary', self.submit))
        lay.addSpacing(6)
        lay.addWidget(_button('New to the system? Create an account', 'link', lambda: window.show_view('register')))
        lay.addSpacing(10)
        # Demo accounts are the ones set up in accounts.py.
        lay.addWidget(ui.label('Prototype demo accounts: dilip.shah@make-it-all.co.uk / Demo-P@ssW0Rd-1# (manager), '
                               'clara.novak@make-it-all.co.uk / Demo-P@ssW0Rd-2# (specialist).', 'small'))

    def submit(self):
        if not self.email.text().strip() or not self.password.text():
            _show(self.error, 'Enter your staff email address and password.')
            return
        employee = accounts.authenticate(self.email.text(), self.password.text())
        self.password.clear()
        if not employee:
            # One message for every failure, so this screen never reveals which emails have accounts.
            _show(self.error, 'Incorrect email address or password.')
            return
        _show(self.error, '')
        self.window.signed_in({k: employee[k] for k in ('id', 'name', 'role', 'teamId')})


class RegisterView(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(ui.label('Create your account', 'h1'))
        lay.addWidget(ui.label('Use your Make-It-All staff email address. This will be your username.', 'lede'))
        lay.addSpacing(8)
        self.formError = _error(lay, 'formError')

        self.email = _field(lay, 'Staff email address')
        self.email.setPlaceholderText('firstname.lastname@make-it-all.co.uk')
        self.emailError = _error(lay)

        self.password = _field(lay, 'Password', password=True)
        show = QCheckBox('Show password')
        lay.addWidget(show)
        self.checklist = QFrame()
        self.checkLay = QVBoxLayout(self.checklist)
        self.checkLay.setContentsMargins(4, 2, 4, 2)
        self.checkLay.setSpacing(2)
        lay.addWidget(self.checklist)

        self.confirm = _field(lay, 'Confirm password', password=True)
        self.confirmError = _error(lay)
        show.toggled.connect(self.toggle_show)

        lay.addSpacing(10)
        lay.addWidget(_button('Create account', 'primary', self.submit))
        lay.addSpacing(6)
        lay.addWidget(_button('Already registered? Sign in', 'link', lambda: window.show_view('signin')))

        self.email.textChanged.connect(self.refresh_checklist)
        self.password.textChanged.connect(self.refresh_checklist)
        self.confirm.returnPressed.connect(self.submit)
        self.refresh_checklist()

    def toggle_show(self, on):
        mode = QLineEdit.Normal if on else QLineEdit.Password
        self.password.setEchoMode(mode)
        self.confirm.setEchoMode(mode)

    def refresh_checklist(self):
        ui.clear(self.checkLay)
        for text, met in auth.passwordRules(self.password.text(), self.email.text()):
            self.checkLay.addWidget(ui.label(('✓ ' if met else '○ ') + text, 'rule ruleMet' if met else 'rule'))

    def submit(self):
        errors = auth.registrationErrors(self.email.text(), self.password.text(), self.confirm.text())
        registration = None
        if not any(errors.values()):
            # R06/R07 checks passed: accounts.py checks for an existing account and sends the code.
            registration = accounts.Registration(self.email.text())
            if not registration.start():
                registration = None
                errors['email'] = 'An account already exists for this email. Each employee can have only one account.'
        self.show_errors(errors)
        if registration:
            password = self.password.text()
            for box in (self.password, self.confirm):
                box.clear()
            self.window.verify(registration, password)

    def show_errors(self, errors):
        _show(self.emailError, errors['email'])
        _show(self.formError, errors['password'])
        _show(self.confirmError, errors['confirm'])
        _markInvalid(self.email, bool(errors['email']))
        _markInvalid(self.password, bool(errors['password']))
        _markInvalid(self.confirm, bool(errors['confirm']))


class VerifyView(QWidget):
    """The 6-digit code step from accounts.py (R08)."""

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.registration = None
        self.password = ''
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(ui.label('Check your email', 'h1'))
        self.lede = ui.label('', 'lede')
        lay.addWidget(self.lede)
        lay.addSpacing(8)
        self.error = _error(lay, 'formError')
        self.code = _field(lay, 'Verification code')
        self.code.setMaxLength(6)
        self.code.returnPressed.connect(self.submit)
        lay.addSpacing(10)
        lay.addWidget(_button('Verify and create account', 'primary', self.submit))
        lay.addSpacing(6)
        lay.addWidget(_button('Back to registration', 'link', lambda: window.show_view('register')))
        lay.addSpacing(10)
        lay.addWidget(ui.label('Prototype: no email is sent, and the code is always 111111.', 'small'))

    def start(self, registration, password):
        self.registration, self.password = registration, password
        self.lede.setText(f'We have sent a 6-digit code to {registration.email}. Enter it below to finish creating your account.')
        self.code.clear()
        _show(self.error, '')

    def submit(self):
        code = self.code.text().strip()
        if not re.fullmatch(r'\d{6}', code):
            _show(self.error, 'Enter the 6-digit code from the email.')
            return
        if not self.registration.verify(code):
            _show(self.error, 'That code is not correct. Check the email and try again.')
            return
        self.registration.set_password(self.password)
        self.password = ''
        self.window.show_view('done')


class DoneView(QWidget):
    def __init__(self, window):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        icon = QLabel('✓')
        icon.setObjectName('bigIcon')
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)
        title = ui.label('Your account is ready', 'h1')
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        message = ui.label('You can now sign in with your staff email address and the password you chose.', 'lede')
        message.setAlignment(Qt.AlignCenter)
        lay.addWidget(message)
        lay.addSpacing(10)
        lay.addWidget(_button('Go to sign in', 'primary', lambda: window.show_view('signin')))


class LoginWindow(QWidget):
    TITLES = {'signin': 'Sign in', 'register': 'Create account', 'verify': 'Verify email', 'done': 'Account created'}

    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setObjectName('loginPage')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(_style())
        self.resize(1280, 860)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 24, 16, 24)
        banner = ui.label('Prototype: registration and password rules are awaiting client confirmation.', 'banner')
        banner.setAlignment(Qt.AlignCenter)
        outer.addWidget(banner)
        outer.addStretch()

        brand = QHBoxLayout()
        brand.addStretch()
        mark = QLabel('M')
        mark.setObjectName('brandMark')
        mark.setFixedSize(30, 30)
        mark.setAlignment(Qt.AlignCenter)
        name = QLabel('Make-It-All')
        name.setStyleSheet('font-weight: bold; font-size: 13pt;')
        brand.addWidget(mark)
        brand.addSpacing(6)
        brand.addWidget(name)
        brand.addStretch()
        outer.addLayout(brand)
        outer.addSpacing(12)

        row = QHBoxLayout()
        row.addStretch()
        card = QFrame()
        card.setObjectName('card')
        card.setFixedWidth(440)
        cardLay = QVBoxLayout(card)
        cardLay.setContentsMargins(28, 26, 28, 26)
        row.addWidget(card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()

        self.views = {'signin': SignInView(self), 'register': RegisterView(self),
                      'verify': VerifyView(self), 'done': DoneView(self)}
        for v in self.views.values():
            cardLay.addWidget(v)
        self.show_view('signin')

    def show_view(self, key):
        # One view in the card at a time; hidden views take no space.
        for name, v in self.views.items():
            v.setVisible(name == key)
        self.current = key
        self.setWindowTitle(self.TITLES[key] + ' – Make-It-All')

    def verify(self, registration, password):
        self.views['verify'].start(registration, password)
        self.show_view('verify')

    def signed_in(self, user):
        self.close()
        self.on_success(user)
