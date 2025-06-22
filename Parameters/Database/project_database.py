from sqlalchemy import create_engine, text
from typing import Any, Union, Optional, List, Dict
from TypeHinting.TypeHint import UserDict
from sqlalchemy.exc import SQLAlchemyError

# Format: mysql+pymysql://<username>:<password>@<host>/
# ( becomes %28
# ) becomes %29
engine = create_engine(
    "mysql+pymysql://UserPython:root%2812345%29@localhost/testlinkclone")


class DatabaseConnector:
    @classmethod
    def return_all_projects(cls) -> list[UserDict]:

        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM projects"))

            # this returns the list of users as a list of dictionaries
            return result.mappings().all()

    @classmethod
    def return_all_projects_names(cls) -> list[UserDict]:

        with engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM projects"))

            # this returns the list of users as a list of dictionaries
            return result.mappings().all()

    @classmethod
    def delete_project_from_database(cls, project_id: int) -> List[dict]:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM projects WHERE id=:id"),
                               {"id": project_id}
                               )

    @classmethod
    def add_project_to_database(cls, ProjectName: str, Description: str, Creator: str, StartDate: str, EndDate: str) -> List[dict]:
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                connection.execute(text("INSERT INTO projects(name, description, owner_name, start_date, end_date) VALUES (:ProjectName, :description, :owner_name, :start_date, :end_date)"),
                                   {"ProjectName": ProjectName,
                                    "description": Description,
                                    "owner_name": Creator,
                                    "start_date": StartDate,
                                    "end_date": EndDate}
                                   )
        except SQLAlchemyError as e:
            print("Database error:", str(e))

    @classmethod
    def return_project_by_name(cls, project_name: str) -> UserDict:

        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM projects WHERE name = :name"),
                                        {"name": project_name})

            return result.mappings().all()[0]

    @classmethod
    def return_project_by_id(cls, id: int) -> UserDict:

        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM projects WHERE id = :id"),
                                        {"id": id})

            return result.mappings().all()[0]
