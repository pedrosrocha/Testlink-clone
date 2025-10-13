from sqlalchemy import text
from typing import Union, Optional
from webapp.TypeHinting.TypeHint import UserDict
from sqlalchemy.exc import SQLAlchemyError
from webapp.config import DatabaseConfig


engine = DatabaseConfig.DBengine


class DatabaseConnector:
    @classmethod
    def return_all_projects(cls) -> Optional[list[UserDict]]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM projects"))
                return result.mappings().all(), ""
        except SQLAlchemyError as e:
            print(f"Database error in return_all_projects: {e}")
            return None, e

    @classmethod
    def return_all_projects_names(cls) -> Union[Optional[list[UserDict]], str]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT name FROM projects"))
                return result.mappings().all(), ""
        except SQLAlchemyError as e:
            print(f"Database error in return_all_projects_names: {e}")
            return None, e

    @classmethod
    def delete_project_from_database(cls, project_id: int) -> Union[bool, str]:
        try:
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM projects WHERE id=:id"),
                                   {"id": project_id})
            return True, ""
        except SQLAlchemyError as e:
            print(f"Database error in delete_project_from_database: {e}")
            return False, e

    @classmethod
    def add_project_to_database(cls, ProjectName: str, Description: str, Creator: str, StartDate: str, EndDate: str) -> bool:
        try:
            with engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO projects(name, description, owner_name, start_date, end_date, updated_by) VALUES (:ProjectName, :description, :owner_name, :start_date, :end_date,:updated_by)"),
                    {"ProjectName": ProjectName,
                     "description": Description,
                     "owner_name": Creator,
                     "start_date": StartDate,
                     "end_date": EndDate,
                     "updated_by": Creator})
            return True, ""
        except SQLAlchemyError as e:
            print(f"Database error in add_project_to_database: {e}")
            return False, e

    @classmethod
    def return_project_by_name(cls, project_name: str) -> Union[Optional[UserDict], str]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM projects WHERE name = :name"),
                                            {"name": project_name})
                return result.mappings().first(), ""
        except SQLAlchemyError as e:
            print(f"Database error in return_project_by_name: {e}")
            return None, e

    @classmethod
    def return_project_by_id(cls, id: int) -> Union[Optional[UserDict], str]:
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT * FROM projects WHERE id = :id"),
                                            {"id": id})

                return result.mappings().first(), ""
        except SQLAlchemyError as e:
            print(f"Database error in return_project_by_id: {e}")
            return None, e

    @classmethod
    def update_project_data(cls, project_id: int, name: str, description: str, status: int, user: str) -> bool:
        try:
            with engine.begin() as connection:
                connection.execute(text(
                    "UPDATE projects SET name =:project, status=:status, description=:description, updated_by=:updated_by WHERE id =:project_id;"),
                    {
                    "status": status,
                    "project": name,
                    "description": description,
                    "updated_by": user,
                    "project_id": project_id
                })
            return True, ""
        except SQLAlchemyError as e:
            print(f"Database error in update_project_data: {e}")
            return False, e

    @classmethod
    def return_first_project(cls) -> Union[Optional[UserDict], str]:
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("SELECT * FROM projects ORDER BY created_at LIMIT 1"))
                return result.mappings().first(), ""
        except SQLAlchemyError as e:
            print(f"Database error in return_first_project: {e}")
            return None, e
