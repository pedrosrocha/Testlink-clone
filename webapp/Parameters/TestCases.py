
from .Database.test_cases_database import DatabaseConnector


class TestCases():
    @classmethod
    def return_testSuits(cls, Projectid):
        pass

    @classmethod
    def add_suite(cls, SuiteName, Description, parent_id, project_id, created_by):
        pass

    @classmethod
    def return_testcases_from_project(cls, parentID):
        return DatabaseConnector.return_all_cases_names_ids(int(parentID))
