"""
session.py - who is logged in.   [was js/session.js]

Part 1 is a static prototype, so the user is hardcoded here.
When the login page (R06/R07) is merged in, it should store the signed-in
user with session.set(user) and these pages will pick it up.
"""
_fallback = {'id': 'E01', 'name': 'Dilip Shah', 'role': 'manager', 'teamId': 'T1'}
_user = None


def get():
    return _user or _fallback


def set(user):
    global _user
    _user = user


def isManager():
    return get()['role'] == 'manager'
