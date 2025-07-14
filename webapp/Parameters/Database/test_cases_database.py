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
    def return_all_cases_names_ids(cls, parentID: int) -> list[UserDict]:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT id, name FROM test_cases WHERE suite_id = :parentID"),
                                        {"parentID": parentID})

            # this returns the list of users as a list of dictionaries
            return result.mappings().all()

    @classmethod
    def delete_test_case_from_database(cls, test_id: int) -> List[dict]:
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                connection.execute(text("DELETE FROM test_cases WHERE id=:id"),
                                   {"id": test_id}
                                   )

            return True
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return False

    @classmethod
    def add_test_case_to_database(cls, suite_id: int, name: str, description: str, preconditions: str, expected_result: str, priority: str, status: str, created_by: str, last_updated_by: str) -> str:
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                query = """
                        INSERT INTO test_cases (suite_id, name, description, preconditions, expected_result, priority, status, created_by, last_updated_by) 
                                                 VALUES (:suite_id, 
                                                 :name, 
                                                 :description, 
                                                 :preconditions, 
                                                 :expected_result, 
                                                 :priority, 
                                                 :status, 
                                                 :created_by, 
                                                 :last_updated_by)
                        """
                result = connection.execute(text(query),
                                            {"suite_id": suite_id,
                                             "name": name,
                                             "description": description,
                                             "preconditions": preconditions,
                                             "expected_result": expected_result,
                                             "priority": priority,
                                             "status": status,
                                             "created_by": created_by,
                                             "last_updated_by": last_updated_by}
                                            )
                # gets the first colomn of the first row (new id)
                return result.lastrowid
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
    def return_testcase_by_id(cls, id: int) -> UserDict:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM test_cases WHERE id = :id"),
                                        {"id": id})

            return result.mappings().all()[0]

    @classmethod
    def update_testcase_data(cls, id: int, updatableItems: str, ItemsValues: UserDict) -> bool:
        try:
            query = "UPDATE test_cases SET " + updatableItems + " WHERE id = " + id + ";"
            with engine.begin() as connection:
                connection.execute(text(query), ItemsValues)

            return True

        except SQLAlchemyError as e:
            print("Database error:", str(e))

        return False
