"""
auth.py - the checks for R06 (registration, staff email as username) and R07 (strong passwords).

The login window (login.py) runs these checks first, then hands over to accounts.py (R08),
which stores the account, sends the verification code and signs people in.
accounts.py expects the login window to check the email format and domain, which is done here.

Every value marked PENDING is waiting on a client forum answer (Posts 1-7),
so each one is a one-line change when the reply arrives.

No Qt in this file, so it can be checked on its own:  python auth.py
"""
import re

from mock_data import employees

config = {
    'STAFF_DOMAINS': ['make-it-all.co.uk'],   # PENDING Post 1: which domains count as staff
    'PASSWORD': {                             # PENDING Post 5: what makes a strong password
        'minLength': 12,
        'upper': True,
        'lower': True,
        'digit': True,
        'symbol': True,
        'notContainingEmail': True,
        'blockCommon': True,
    },
}
cfg = config

COMMON_PASSWORDS = {
    'password123!', 'password1234', 'password1234!', 'qwerty123456',
    '123456789012', 'letmein12345!', 'welcome12345!', 'makeitall123!',
}


def normaliseEmail(email):
    # Same as accounts.py: capitals are ignored (PENDING Post 4).
    return email.strip().lower()


def onStaffList(email):
    email = normaliseEmail(email)
    return any(e['email'].lower() == email for e in employees)


def emailProblem(email):
    """'' if the email passes R06's checks, otherwise the message to show.
    Whether it already has an account is checked by accounts.Registration.start()."""
    email = normaliseEmail(email)
    if not email:
        return 'Enter your staff email address.'
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        return 'Enter a valid email address, for example name@make-it-all.co.uk.'
    if email.split('@')[1] not in cfg['STAFF_DOMAINS']:
        return 'Only Make-It-All staff can register. Use your staff email address.'
    if not onStaffList(email):
        return 'We could not find this email in the staff directory. Check it is your own staff email address.'
    return ''


def passwordRules(password, email=''):
    """One (label, met) pair per active rule, so the on-screen checklist always matches config."""
    p = cfg['PASSWORD']
    rules = []
    if p['minLength']:
        rules.append((f"At least {p['minLength']} characters", len(password) >= p['minLength']))
    if p['upper']:
        rules.append(('An upper-case letter (A-Z)', bool(re.search(r'[A-Z]', password))))
    if p['lower']:
        rules.append(('A lower-case letter (a-z)', bool(re.search(r'[a-z]', password))))
    if p['digit']:
        rules.append(('A number (0-9)', bool(re.search(r'[0-9]', password))))
    if p['symbol']:
        rules.append(('A symbol (for example ! # ? %)', bool(re.search(r'[^A-Za-z0-9]', password))))
    if p['notContainingEmail']:
        local = email.split('@')[0].lower()
        parts = [part for part in re.split(r'[._-]', local) if len(part) >= 3]
        contains = any(part in password.lower() for part in parts)
        rules.append(('Does not contain your email name', bool(password) and not contains))
    if p['blockCommon']:
        rules.append(('Not a commonly used password', bool(password) and password.lower() not in COMMON_PASSWORDS))
    return rules


def passwordOk(password, email=''):
    return all(met for _, met in passwordRules(password, email))


def registrationErrors(email, password, confirm):
    """Messages to show for each field; all empty means the form can go to accounts.py."""
    errors = {'email': emailProblem(email), 'password': '', 'confirm': ''}
    if not passwordOk(password, email):
        errors['password'] = 'Your password does not meet all the requirements below.'
    elif password != confirm:
        errors['confirm'] = 'The passwords do not match.'
    return errors


if __name__ == '__main__':
    # Quick check without the GUI:  python auth.py
    checks = [
        ('outsider rejected', emailProblem('bob@gmail.com') != ''),
        ('company address not on the staff list rejected', emailProblem('jane.doe@make-it-all.co.uk') != ''),
        ('staff email accepted (any capitals)', emailProblem('Ruth.Adeyemi@Make-It-All.co.uk') == ''),
        ('short password rejected', not passwordOk('Ab1!', 'ruth.adeyemi@make-it-all.co.uk')),
        ('password with own name rejected', not passwordOk('Ruth#Passw0rd1', 'ruth.adeyemi@make-it-all.co.uk')),
        ('common password rejected', not passwordOk('Password123!', 'ruth.adeyemi@make-it-all.co.uk')),
        ('strong password accepted', passwordOk('Str0ng#Passw0rd', 'ruth.adeyemi@make-it-all.co.uk')),
        ('mismatch caught', registrationErrors('ruth.adeyemi@make-it-all.co.uk', 'Str0ng#Passw0rd', 'x')['confirm'] != ''),
    ]
    for name, ok in checks:
        print(('PASS ' if ok else 'FAIL ') + name)
