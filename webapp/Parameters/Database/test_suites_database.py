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
    def return_all_suites_names_ids(cls, projectID) -> list[UserDict]:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT id, name, parent_suite_id FROM test_suites WHERE project_id = :id"),
                                        {"id": projectID})

            # this returns the list of users as a list of dictionaries
            return result.mappings().all()

    @classmethod
    # FAKE
    def delete_project_from_database(cls, project_id: int) -> List[dict]:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM projects WHERE id=:id"),
                               {"id": project_id}
                               )

    @classmethod
    def add_suite_to_database(cls, SuiteName: str, Description: str, Creator: str, Project_id: int, ParentID: str) -> List[dict]:
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                connection.execute(text("INSERT INTO test_suites (project_id, parent_suite_id, name, description, created_by) VALUES (:Project_id, :ParentID,:SuiteName,:description,:owner_name)"),
                                   {"SuiteName": SuiteName,
                                    "description": Description,
                                    "owner_name": Creator,
                                    "Project_id": Project_id,
                                    "ParentID": ParentID,
                                    "updated_by": Creator}
                                   )
        except SQLAlchemyError as e:
            print("Database error:", str(e))

    @classmethod
    def return_project_by_name(cls, project_name: str) -> UserDict:
        # FAKE

        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM projects WHERE name = :name"),
                                        {"name": project_name})

            return result.mappings().all()[0]

    @classmethod
    def return_project_by_id(cls, id: int) -> UserDict:
        # FAKE

        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM projects WHERE id = :id"),
                                        {"id": id})

            return result.mappings().all()[0]

    @classmethod
    def update_project_data(cls, name: str, description: str, status: int, user: str) -> bool:
        # FAKE
        try:
            with engine.begin() as connection:
                connection.execute(text("UPDATE projects SET status=:status, description=:description, updated_by=:updated_by WHERE name =:project;"),
                                   {
                    "status": status,
                    "project": name,
                    "description": description,
                    "updated_by": user
                })

            return True

        except SQLAlchemyError as e:
            print("Database error:", str(e))

        return False
