"""
From the login window, if user is logging in, call authenticate(), which returns the employee dict if password matches account, None if not.
To register a new user, create a Registration(email) object and call start(). It sends a verification code to the email and 
returns True if email is valid and not already registered, then call verify(code), then set_password(pw).

Assumed that login window will handle logic for validating email format and domain. 
verification code must be 6 digit string.
_demo_accounts and _accounts will be replaced in prod.

"""
import hashlib
from mock_data import employees


def _find_employee(email):
    for e in employees:
        if e['email'] == email:
         return e
    return None

_demo_accounts = {                                    
    'dilip.shah@make-it-all.co.uk': 'Demo-P@ssW0Rd-1#',
    'clara.novak@make-it-all.co.uk': 'Demo-P@ssW0Rd-2#',
}

def _normalise(email):
    return email.strip().lower()

def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

_accounts = {email: _hash(pw) for email, pw in _demo_accounts.items()}   



def authenticate(email, password):
    """ call this function from login window for users already registered"""
    email = _normalise(email)
    stored = _accounts.get(email)
    if stored is None or stored != _hash(password):
        return None
    return _find_employee(email)



class Registration:
    """Create with an email, call start(), then verify(code), then set_password(pw)."""

    def __init__(self, email):
        self.email = _normalise(email)
        self._code = None
        self._verified = False

    def start(self):
       
        if _find_employee(self.email) is None or self.email in _accounts:
            return False
        self._code = self._generate_code()
        self._send_code()
        return True

    def verify(self, code):
      
        if self._code is None:
            return False
        self._verified = code.strip() == self._code
        return self._verified

    def set_password(self, password):
        
        if not self._verified or self.email in _accounts:
            return False
        _accounts[self.email] = _hash(password)
        self._code = None                         # registration finished, can't reset password
        self._verified = False
        return True

    def _generate_code(self):
        return '111111'                           # prototype stand-in

    def _send_code(self):
        pass                                      # prototype stand-in