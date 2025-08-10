from sqlalchemy import create_engine, text
from typing import Any, Union, Optional, List, Dict
from webapp.TypeHinting.TypeHint import UserDict
from sqlalchemy.exc import SQLAlchemyError


# Format: mysql+pymysql://<username>:<password>@<host>/
# ( becomes %28
# ) becomes %29
engine = create_engine(
    "mysql+pymysql://UserPython:root%2812345%29@localhost/testlinkclone")


class DatabaseConnector:

    @classmethod
    def return_steps_from_testcase(cls, test_case_id: int, test_case_version: int) -> list[UserDict]:
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("""
                        SELECT * 
                        FROM test_steps 
                        WHERE test_case_version_id = :id 
                        AND version = :version
                    """),
                    {"id": test_case_id, "version": test_case_version}
                )

                steps = result.mappings().all()  # Always returns a list
                return steps  # Could be [], which is valid

        except SQLAlchemyError as e:
            # Here we log the error and re-raise or wrap in custom exception
            # You could also integrate logging with your app's logger
            print(f"Database error while retrieving steps: {e}")
            raise RuntimeError("Error retrieving steps from database") from e


'''
    @classmethod
    def add_user(cls, username: str, encrypted_password: str, email: str) -> None:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                connection.execute(text("INSERT INTO users(username, email, password_hash) VALUES (:username, :email, :password_hash)"),
                                   {"username": username,
                                    "email": email,
                                    "password_hash": encrypted_password}
                                   )
        except SQLAlchemyError as e:
            print("Database error:", str(e))

    @classmethod
    def delete_user_from_database(cls, user_id: int) -> List[dict]:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM users WHERE id=:id"),
                               {"id": user_id}
                               )

    @classmethod
    def return_user_info(cls, username: str) -> UserDict:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users WHERE username = :username"),
                                        {"username": username})

            # this returns the list of users as a dictionary
            DictFromUser = result.mappings().first()
            return DictFromUser if DictFromUser else None

    @classmethod
    def get_by_id(cls, id: int) -> None:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users WHERE id = :id"),
                                        {"id": id})

            # this returns the list of users as a dictionary
            DictFromUser = result.mappings().first()
            return DictFromUser if DictFromUser else None

    @classmethod
    def change_user_password(cls, username: str, password_hash: str) -> None:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        with engine.begin() as connection:
            connection.execute(text("UPDATE users SET password_hash = :password_hash WHERE username = :username"),
                               {"password_hash": password_hash,
                                "username": username
                                })

    @classmethod
    def change_user_level(cls, user_id, user_level):
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        with engine.begin() as connection:
            connection.execute(text("UPDATE users SET user_level = :user_level WHERE id = :id"),
                               {"id": user_id,
                                "user_level": user_level
                                })

    @classmethod
    def filter_by_level(cls, user_level):
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users WHERE user_level = :UserLevel"),
                                        {"UserLevel": user_level})

            # this returns the list of users as a dictionary
            DictFromUser = result.mappings().all()
            return DictFromUser if DictFromUser else None

'''
