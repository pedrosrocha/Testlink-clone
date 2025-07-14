from sqlalchemy import create_engine, text
from typing import List
from webapp.TypeHinting.TypeHint import UserDict
from sqlalchemy.exc import SQLAlchemyError

# Format: mysql+pymysql://<username>:<password>@<host>/
# ( becomes %28
# ) becomes %29
engine = create_engine(
    "mysql+pymysql://UserPython:root%2812345%29@localhost/testlinkclone")


class DatabaseConnector:
    @classmethod
    def return_all_suites_from_project(cls, projectID) -> list[UserDict]:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM test_suites WHERE project_id = :id"),
                                        {"id": projectID})

            # this returns the list of users as a list of dictionaries
            return result.mappings().all()

    @classmethod
    def return_all_suites_names_ids(cls, projectID: int, parentID: int) -> list[UserDict]:
        if parentID:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT id, name FROM test_suites WHERE project_id = :id AND parent_suite_id = :parentID"),
                                            {"id": projectID,
                                            "parentID": parentID})

                # this returns the list of users as a list of dictionaries
                return result.mappings().all()

        with engine.connect() as connection:
            result = connection.execute(text("SELECT id, name FROM test_suites WHERE project_id = :id AND parent_suite_id IS null"),
                                        {"id": projectID})

            # this returns the list of users as a list of dictionaries
            return result.mappings().all()

    @classmethod
    def delete_suite_from_database(cls, suite_id: int) -> List[dict]:
        try:
            # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM test_suites WHERE id=:id"),
                                   {"id": suite_id}
                                   )
            return True
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return False

    @classmethod
    def add_suite_to_database(cls, SuiteName: str, Description: str, Creator: str, Project_id: int, ParentID: str) -> List[dict]:
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
                return result.lastrowid
        except SQLAlchemyError as e:
            print("Database error:", str(e))

    @classmethod
    def return_project_by_name(cls, project_name: str) -> UserDict:
        # FAKE

        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM test_suites WHERE name = :name"),
                                        {"name": project_name})

            return result.mappings().all()[0]

    @classmethod
    def return_suite_by_id(cls, id: int) -> UserDict:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM test_suites WHERE id = :id"),
                                        {"id": id})

            return result.mappings().all()[0]

    @classmethod
    def update_suite_data(cls, id: int, updatableItems: str, ItemsValues: UserDict) -> bool:
        try:
            query = "UPDATE test_suites SET " + updatableItems + " WHERE id = " + id + ";"
            with engine.begin() as connection:
                connection.execute(text(query), ItemsValues)

            return True

        except SQLAlchemyError as e:
            print("Database error:", str(e))

        return False
