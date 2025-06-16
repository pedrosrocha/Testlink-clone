from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from .user_database import DatabaseConnector


class testclone_user_list():
    def __init__(self, app):
        self.bcrypt = Bcrypt(app)

    def add_user(self, username, password, email):
        encrypted_password = self.bcrypt.generate_password_hash(
            password).decode('utf-8')
        DatabaseConnector.add_user(username, encrypted_password, email)

    def return_users(self):
        return DatabaseConnector.return_all_users()

    def delete_user(self, user_id):
        DatabaseConnector.delete_user_from_database(int(user_id))

    def return_user_by_username(self, username):
        return DatabaseConnector.return_user_info(username)

    def get_by_id(self, id):
        return DatabaseConnector.get_by_id(id)

    def is_user_valid(self, username, password):
        user_found_in_database = self.return_user_by_username(username)

        if not user_found_in_database:
            return False

        if username == user_found_in_database["username"] and self.bcrypt.check_password_hash(user_found_in_database["password_hash"], password):
            return True

        return False


class testclone_user(UserMixin):
    """Flask-Login User wrapper."""

    def __init__(self, id, username):
        self.id = id
        self.username = username

    @classmethod
    def from_dict(cls, user_data):
        return cls(id=user_data['id'],
                   username=user_data['username'])
