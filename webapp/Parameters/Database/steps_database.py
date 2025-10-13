from sqlalchemy import text
from typing import Union, List, Dict, Tuple
from sqlalchemy.exc import SQLAlchemyError
from webapp.config import DatabaseConfig


engine = DatabaseConfig.DBengine


class DatabaseConnector:
    @classmethod
    def return_step_by_id(cls, step_id: int) -> Union[Tuple[Dict, str], Tuple[bool, str]]:
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("""
                        SELECT * 
                        FROM test_steps 
                        WHERE id = :id 
                    """),
                    {"id": step_id}
                )

                steps = result.mappings().all()[0]
                return steps, ""

        except SQLAlchemyError as e:
            # Here we log the error and re-raise or wrap in custom exception
            print(f"Database error while retrieving steps: {e}")
            return False, e

    @classmethod
    def return_steps_from_testcase(cls, test_case_id: int, test_case_version: int) -> Union[Tuple[Dict, str], Tuple[bool, str]]:
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("""
                        SELECT * 
                        FROM test_steps 
                        WHERE test_case_version_id = :id 
                        AND version = :version
                        ORDER BY step_position
                    """),
                    {"id": test_case_id, "version": test_case_version}
                )

                steps = result.mappings().all()
                return steps, ""

        except SQLAlchemyError as e:
            print(f"Database error while retrieving steps: {e}")
            return False, e

    @classmethod
    def update_step_data(cls, id: int, actions: str, results: str) -> Union[bool, str]:
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        with engine.begin() as connection:
            try:
                connection.execute(text("UPDATE test_steps SET step_action = :step_action, expected_value = :expected_value WHERE id = :id"),
                                   {"step_action": actions,
                                    "expected_value": results,
                                    "id": id
                                    })
                return False
            except SQLAlchemyError as e:
                # Here we log the error and re-raise or wrap in custom exception
                print(f"Database error while retrieving steps: {e}")
                return e

    @classmethod
    def create_new_step(cls, version: int, test_id: int, actions_data: str, results_data: str, position: int) -> Union[Tuple[int, str], Tuple[bool, str]]:
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        try:
            with engine.begin() as connection:
                result = connection.execute(text("INSERT INTO test_steps(test_case_version_id, step_position, step_action, expected_value, version) VALUES(:test_id, :position, :actions_data, :results_data, :version)"),
                                            {
                    "version": version,
                    "test_id": test_id,
                    "actions_data": actions_data,
                    "results_data": results_data,
                    "position": position
                })

                return result.lastrowid, ""
        except SQLAlchemyError as e:
            print("Database error:", str(e))
            return False, e

    @classmethod
    def update_step_position(cls, id: int, position: int):
        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        with engine.begin() as connection:
            try:
                connection.execute(text("UPDATE test_steps SET step_position = :position WHERE id = :id"),
                                   {"position": position,
                                    "id": id
                                    })
                return False

            except SQLAlchemyError as e:
                # Here we log the error and re-raise or wrap in custom exception
                print(f"Database error while retrieving steps: {e}")
                return e

    @classmethod
    def delete_test_step_from_database(cls, id: int) -> List[dict]:

        # engine.begin() commits the transaction automatically. It also rollsback in a case of an error
        with engine.begin() as connection:
            try:
                connection.execute(text("DELETE FROM test_steps WHERE id=:id"),
                                   {"id": id}
                                   )
                return False
            except SQLAlchemyError as e:
                print(f"Database error while retrieving steps: {e}")
                return e

    @classmethod
    def return_step_by_info(cls, position: int, testcase_id: int, version: int) -> Union[Tuple[Dict, str], Tuple[bool, str]]:
        try:
            with engine.connect() as connection:
                result = connection.execute(
                    text("""
                        SELECT step_action, expected_value
                        FROM test_steps 
                        WHERE test_case_version_id = :id 
                        AND version = :version
                        AND step_position = :position
                    """),
                    {"position": position,
                     "id": testcase_id,
                     "version": version
                     }
                )
                result_list = result.mappings().all()
                if not result_list:
                    return False, "no step found."

                step = result_list[0]
                return step, ""

        except SQLAlchemyError as e:
            # Here we log the error and re-raise or wrap in custom exception
            print(f"Database error while retrieving steps: {e}")
            return False, e
