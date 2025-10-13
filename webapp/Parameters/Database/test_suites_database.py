from sqlalchemy import text
from webapp.TypeHinting.TypeHint import UserDict
from typing import Union, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError
from webapp.config import DatabaseConfig


engine = DatabaseConfig.DBengine


class DatabaseConnector:
    @classmethod
    def return_all_suites_from_project(cls, projectID) -> Union[Tuple[list[UserDict], str], Tuple[bool, SQLAlchemyError]]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM test_suites WHERE project_id = :id"),
                                            {"id": projectID})

                # this returns the list of users as a list of dictionaries
                return result.mappings().all(), ""
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return False, e

    @classmethod
    def return_all_suites_names_ids(cls, projectID: int, parentID: int) -> Union[Tuple[list[UserDict], str], Tuple[bool, SQLAlchemyError]]:
        if parentID:
            try:
                with engine.connect() as connection:
                    result = connection.execute(text("SELECT id, name FROM test_suites WHERE project_id = :id AND parent_suite_id = :parentID"),
                                                {"id": projectID,
                                                "parentID": parentID})

                    # this returns the list of users as a list of dictionaries
                    return result.mappings().all(), ""
            except SQLAlchemyError as e:
                print(f"Database error: {e}")
                return False, e

        with engine.connect() as connection:
            try:
                result = connection.execute(text("SELECT id, name FROM test_suites WHERE project_id = :id AND parent_suite_id IS null"),
                                            {"id": projectID})

                # this returns the list of users as a list of dictionaries
                return result.mappings().all(), ""
            except SQLAlchemyError as e:
                print(f"Database error: {e}")
                return False, e

    @classmethod
    def delete_suite_from_database(cls, suite_id: int) -> Union[Tuple[bool, str], Tuple[bool, SQLAlchemyError]]:
        try:
            # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM test_suites WHERE id=:id"),
                                   {"id": suite_id}
                                   )
            return True, ""
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return False, e

    @classmethod
    def add_suite_to_database(cls, SuiteName: str, Description: str, Creator: str, Project_id: int, ParentID: str) -> Union[Tuple[int, str], Tuple[bool, SQLAlchemyError]]:
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                result = connection.execute(text("INSERT INTO test_suites (project_id, parent_suite_id, name, description, created_by) VALUES (:Project_id, :ParentID,:SuiteName,:description,:owner_name)"),
                                            {"SuiteName": SuiteName,
                                             "description": Description,
                                             "owner_name": Creator,
                                             "Project_id": Project_id,
                                             "ParentID": ParentID,
                                             "updated_by": Creator}
                                            )
                # gets the first colomn of the first row (new id)
                return result.lastrowid, ""
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return False, e

    @classmethod
    def return_suite_by_id(cls, id: int) -> Union[Tuple[UserDict, str], Tuple[bool, SQLAlchemyError]]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM test_suites WHERE id = :id"),
                                            {"id": id})

                return result.mappings().all()[0], ""
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return False, e

    @classmethod
    def update_suite_data(cls, updatableItems: str, ItemsValues: UserDict) -> Optional[SQLAlchemyError]:
        try:
            query = "UPDATE test_suites SET " + updatableItems + " WHERE id = :id;"
            with engine.begin() as connection:
                connection.execute(text(query), ItemsValues)

            return None

        except SQLAlchemyError as e:
            print("Database error:", str(e))

        return e
