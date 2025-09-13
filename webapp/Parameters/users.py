from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from .Database.user_database import DatabaseConnector
from ..utils.return_data_model import DatabaseReturnValueModel


class testclone_user_list():
    def __init__(self, crypt):
        # self.bcrypt = Bcrypt(app)
        self.bcrypt = crypt

    def add_user(self, username, password, email) -> DatabaseReturnValueModel:
        for user in self.return_users().data:
            # If the user already exists, another username mus be chosen
            if user['username'] == username:
                return DatabaseReturnValueModel(
                    executed=False,
                    message="Not possible to add user.",
                    error=f"The name {username} is duplicated."
                )

        encrypted_password = self.bcrypt.generate_password_hash(
            password).decode('utf-8')

        error = DatabaseConnector.add_user(username, encrypted_password, email)

        if not error:
            return DatabaseReturnValueModel(
                executed=True,
                message="User added sucessfully",
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="It was not possible to add user",
            error=error
        )

    def return_users(self) -> DatabaseReturnValueModel:
        users, err = DatabaseConnector.return_all_users()

        if not users:
            return DatabaseReturnValueModel(
                executed=False,
                message="No users found.",
                data=users,
                error=err
            )
        return DatabaseReturnValueModel(
            executed=True,
            message="Users found.",
            data=users,
        )

    def delete_user(self, user_id) -> DatabaseReturnValueModel:
        # find user by id
        # if user == admin and number of admin = 1
        # return false
        # else database
        user, error = DatabaseConnector.get_user_by_id(int(user_id))

        if error:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"No user found for the id {user_id}",
                error=error
            )

        admins_users, err = DatabaseConnector.filter_by_level("admin")

        if err:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"Not possible to delete the user",
                error="No admin users found."
            )

        if user['user_level'] == 'admin' and len(admins_users) < 2:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"Not possible to delete the user",
                error="There must be at least 1 admin user."
            )

        DatabaseConnector.delete_user_from_database(int(user_id))
        return DatabaseReturnValueModel(
            executed=True,
            message=f"User {user_id} deleted successfuly",
        )

    def return_user_by_username(self, username: str) -> DatabaseReturnValueModel:
        user_info, error = DatabaseConnector.return_user_info(username)
        if error:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"No user found for the username {username}",
                error=error
            )
        return DatabaseReturnValueModel(
            executed=True,
            message=f"User found for the username {username}",
            data=user_info
        )

    def get_by_id(self, id) -> DatabaseReturnValueModel:
        user, error = DatabaseConnector.get_user_by_id(int(id))

        if error:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"No user found for th id {id}",
                error=error
            )

        return DatabaseReturnValueModel(
            executed=True,
            message=f"No user found for this id",
            data=user
        )

    def is_user_valid(self, username, password) -> DatabaseReturnValueModel:

        user_found_in_database = self.return_user_by_username(username)

        if not user_found_in_database.data:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"No user found with the name {username}",
                error=user_found_in_database.error
            )

        if username == user_found_in_database.data["username"] and self.bcrypt.check_password_hash(user_found_in_database.data["password_hash"], password):
            return DatabaseReturnValueModel(
                executed=True,
                message=f"User {username} and password validated",
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="Not possible to validate the user.\n",
            error=f"Wrong password for the user {username}",
        )

    def change_user_password(self, username, password) -> DatabaseReturnValueModel:
        password_hash = self.bcrypt.generate_password_hash(
            password).decode('utf-8')
        error = DatabaseConnector.change_user_password(username, password_hash)
        if error:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"Not possible to chnsge the password {username}",
                error=error
            )
        return DatabaseReturnValueModel(
            executed=True,
            message=f"Password for the {username} changed successfuly",
        )

    def change_user_level(self, user_id, user_level) -> DatabaseReturnValueModel:
        users = self.return_users().data
        admin_users = [user for user in users if user['user_level'] == 'admin']

        user_id = int(user_id)
        # If the current user being changed from admin to another user level is the last admin, the change will be forbidden.
        # As there are changes that one the admin can make, this will be forbidden by the software
        if len(admin_users) == 1 and admin_users[0]['id'] == user_id and user_level != 'admin':
            return DatabaseReturnValueModel(
                executed=False,
                message="Not possible to chnage the level of this user.",
                error="There must be at leat 1 admin in the system."
            )

        error = DatabaseConnector.change_user_level(user_id, user_level)
        if error:
            return DatabaseReturnValueModel(
                executed=False,
                message="Not possible to chnage the level of this user",
                error=error
            )
        return DatabaseReturnValueModel(
            executed=True,
            message="User level changed successfult",
        )


class testclone_user(UserMixin):
    """Flask-Login User wrapper."""

    def __init__(self, id, username, user_level):
        self.id = id
        self.username = username
        self.user_level = user_level

    @classmethod
    def from_dict(cls, user_data):
        return cls(
            id=user_data['id'],
            username=user_data['username'],
            user_level=user_data['user_level']
        )
