from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from .Database.user_database import DatabaseConnector


class testclone_user_list():
    def __init__(self, app):
        self.bcrypt = Bcrypt(app)

    def add_user(self, username, password, email):
        for user in self.return_users():
            # If the user already exists, another username mus be chosen
            if user['username'] == username:
                return False

        encrypted_password = self.bcrypt.generate_password_hash(
            password).decode('utf-8')
        DatabaseConnector.add_user(username, encrypted_password, email)
        return True

    def return_users(self):
        return DatabaseConnector.return_all_users()

    def delete_user(self, user_id):
        DatabaseConnector.delete_user_from_database(int(user_id))

    def return_user_by_username(self, username):
        return DatabaseConnector.return_user_info(username)

    def get_by_id(self, id):
        return DatabaseConnector.get_by_id(int(id))

    def is_user_valid(self, username, password):
        user_found_in_database = self.return_user_by_username(username)

        if not user_found_in_database:
            return False

        if username == user_found_in_database["username"] and self.bcrypt.check_password_hash(user_found_in_database["password_hash"], password):
            return True

        return False

    def change_user_password(self, username, password):
        password_hash = self.bcrypt.generate_password_hash(
            password).decode('utf-8')
        DatabaseConnector.change_user_password(username, password_hash)

    def change_user_level(self, user_id, user_level):
        users = self.return_users()
        admin_users = [user for user in users if user['user_level'] == 'admin']

        user_id = int(user_id)
        # If the current user being changed from admin to another user level is the last admin, the change will be forbidden.
        # As there are changes that one the admin can make, this will be forbidden by the software
        if len(admin_users) == 1 and admin_users[0]['id'] == user_id and user_level != 'admin':
            return False

        DatabaseConnector.change_user_level(user_id, user_level)
        return True


class testclone_user(UserMixin):
    """Flask-Login User wrapper."""

    def __init__(self, id, username, user_level):
        self.id = id
        self.username = username
        self.user_level = user_level

    @classmethod
    def from_dict(cls, user_data):
        return cls(id=user_data['id'],
                   username=user_data['username'],
                   user_level=user_data['user_level']
                   )
