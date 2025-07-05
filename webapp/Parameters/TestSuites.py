
from .Database.test_suites_database import DatabaseConnector


class TestSuits():
    @classmethod
    def return_testSuits(cls, Projectid):
        pass

    @classmethod
    def add_suite(cls, SuiteName, Description, parent_id, project_id, created_by):
        if parent_id:
            DatabaseConnector.add_suite_to_database(
                SuiteName, Description, created_by, int(project_id), int(parent_id))

        else:
            DatabaseConnector.add_suite_to_database(
                SuiteName, Description, created_by, int(project_id), None)
