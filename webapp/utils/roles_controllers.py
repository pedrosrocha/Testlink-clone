from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.user_level not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
