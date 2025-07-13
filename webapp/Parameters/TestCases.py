
from .Database.test_cases_database import DatabaseConnector


class TestCases():
    @classmethod
    def return_testSuits(cls, Projectid):
        pass

    @classmethod
    def add_testcase(cls, test_name, Description, precondition, expected_result, status, priority, suite_id, created_by, last_updated_by):
        if (not status):
            status = "draft"

        if (not priority):
            priority = "high"

        return DatabaseConnector.add_test_case_to_database(
            int(suite_id),
            test_name,
            Description,
            precondition,
            expected_result,
            priority,
            status,
            created_by,
            last_updated_by)

    @classmethod
    def return_testcases_from_project(cls, parentID):
        return DatabaseConnector.return_all_cases_names_ids(int(parentID))

    @classmethod
    def update_testcase_data(cls, id, name=None, suite_id=None, description=None, precondition=None, expected_result=None, priority=None, status=None, last_updated_by=None):
        UpdatableItems = ""
        ItemsValues = {}

        if name:
            UpdatableItems = UpdatableItems + "name = :name,"
            ItemsValues["name"] = name
        if suite_id:
            UpdatableItems = UpdatableItems + "suite_id = :suite_id,"
            ItemsValues["suite_id"] = suite_id
        if description:
            UpdatableItems = UpdatableItems + "description = :description,"
            ItemsValues["description"] = description
        if precondition:
            UpdatableItems = UpdatableItems + "precondition = :precondition,"
            ItemsValues["precondition"] = precondition
        if expected_result:
            UpdatableItems = UpdatableItems + "expected_result = :expected_result,"
            ItemsValues["expected_result"] = expected_result
        if priority:
            UpdatableItems = UpdatableItems + "priority = :priority,"
            ItemsValues["priority"] = priority
        if status:
            UpdatableItems = UpdatableItems + "status = :status,"
            ItemsValues["status"] = status
        if last_updated_by:
            UpdatableItems = UpdatableItems + "last_updated_by = :last_updated_by,"
            ItemsValues["last_updated_by"] = last_updated_by

        # removes the "," (comma) from the UpdatableItems top avoid SQL errors
        if (UpdatableItems[-1] == ","):
            UpdatableItems = UpdatableItems[:-1]

        if (UpdatableItems):
            return DatabaseConnector.update_testcase_data(str(id), UpdatableItems, ItemsValues)
        return False
