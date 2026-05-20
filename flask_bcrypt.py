from werkzeug.security import check_password_hash as _check_password_hash
from werkzeug.security import generate_password_hash as _generate_password_hash


def generate_password_hash(password, rounds=12):
    hashed = _generate_password_hash(password)
    return hashed.encode("utf-8") if isinstance(hashed, str) else hashed


def check_password_hash(pw_hash, password):
    if isinstance(pw_hash, bytes):
        pw_hash = pw_hash.decode("utf-8")
    return _check_password_hash(pw_hash, password)


class Bcrypt:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.extensions = getattr(app, "extensions", {})
        app.extensions["bcrypt"] = self

    def generate_password_hash(self, password, rounds=12):
        return generate_password_hash(password, rounds=rounds)

    def check_password_hash(self, pw_hash, password):
        return check_password_hash(pw_hash, password)
