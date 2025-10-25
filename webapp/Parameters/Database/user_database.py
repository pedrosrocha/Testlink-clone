from sqlalchemy import text
from typing import Union, Optional, List, Dict, Tuple
from webapp.TypeHinting.TypeHint import UserDict
from sqlalchemy.exc import SQLAlchemyError
from webapp.config import DatabaseConfig


engine = DatabaseConfig.DBengine


class DatabaseConnector:

    @classmethod
    def return_all_users(cls) -> Tuple[list[UserDict], str]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM users"))
                # this returns the list of users as a list of dictionaries
                return result.mappings().all(), ""
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return False, e

    @classmethod
    def add_user(cls, username: str, encrypted_password: str, email: str) -> str:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                connection.execute(text("INSERT INTO users(username, email, password_hash) VALUES (:username, :email, :password_hash)"),
                                   {"username": username,
                                    "email": email,
                                    "password_hash": encrypted_password}
                                   )
                return ""
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return e

    @classmethod
    def delete_user_from_database(cls, user_id: int) -> List[dict]:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM users WHERE id=:id"),
                                   {"id": user_id}
                                   )
                return False
        except SQLAlchemyError as e:
            print(f'Database error: {e}')
            return e

    @classmethod
    def return_user_info(cls, username: str) -> Tuple[Union[Dict, bool], str]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM users WHERE username = :username"),
                                            {"username": username})

                # this returns the list of users as a dictionary
                DictFromUser = result.mappings().first()

                if DictFromUser:
                    return DictFromUser, ""
                 
                return None, "No user found"
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return False, e

    @classmethod
    def get_user_by_id(cls, id: int) -> Tuple[Union[Dict, bool], str]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM users WHERE id = :id"),
                                            {"id": id})

                # this returns the list of users as a dictionary
                DictFromUser = result.mappings().first()
                return DictFromUser, ""

        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return False, e

    @classmethod
    def change_user_password(cls, username: str, password_hash: str) -> Optional[str]:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                connection.execute(text("UPDATE users SET password_hash = :password_hash WHERE username = :username"),
                                   {"password_hash": password_hash,
                                    "username": username
                                    })
                return None
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return e

    @classmethod
    def change_user_level(cls, user_id, user_level) -> Optional[str]:
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                connection.execute(text("UPDATE users SET user_level = :user_level WHERE id = :id"),
                                   {"id": user_id,
                                    "user_level": user_level
                                    })
                return None
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return e

    @classmethod
    def filter_by_level(cls, user_level) -> Tuple[Union[List[Dict], str]]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM users WHERE user_level = :UserLevel"),
                                            {"UserLevel": user_level})

                # this returns the list of users as a dictionary
                DictFromUser = result.mappings().all()
                return DictFromUser, ""
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return False, e
