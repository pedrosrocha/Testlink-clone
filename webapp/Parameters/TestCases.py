
from .Database.test_cases_database import DatabaseConnector
from datetime import datetime


class TestCases():
    @classmethod
    def return_testcase_by_id(cls, testcase_id):
        testDict = dict(
            DatabaseConnector.return_testcase_by_id(int(testcase_id)))
        versions_list = testDict["versions"].split(',')
        testDict['versions'] = versions_list
        return testDict

    @classmethod
    def copy_test_case(cls, parent_id, testcase_id, current_user):
        copied_testcase = cls.return_testcase_by_id(int(testcase_id))
        testcases_inside_parent = DatabaseConnector.return_all_cases_names_ids(
            int(parent_id))

        if not copied_testcase:
            return False

        newName = copied_testcase["name"]

        for test in testcases_inside_parent:
            if test["name"] == copied_testcase["name"]:
                current_datetime = datetime.now()
                newName = current_datetime.ctime() + " : " + newName
                break

        cls.add_testcase(newName,
                         copied_testcase["description"],
                         copied_testcase["preconditions"],
                         copied_testcase["expected_result"],
                         copied_testcase["status"],
                         copied_testcase["priority"],
                         parent_id,
                         current_user,
                         current_user)
        return True

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
    def update_testcase_data(cls, id, name=None, suite_id=None, description=None, precondition=None, expected_result=None, priority=None, status=None, last_updated_by=None, versions=None, current_version=None):
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
            UpdatableItems = UpdatableItems + "preconditions = :precondition,"
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
        if versions:
            UpdatableItems = UpdatableItems + "versions = :versions,"
            ItemsValues["versions"] = versions
        if current_version:
            UpdatableItems = UpdatableItems + "current_version = :current_version,"
            ItemsValues["current_version"] = current_version

        # removes the "," (comma) from the UpdatableItems top avoid SQL errors
        if (UpdatableItems[-1] == ","):
            UpdatableItems = UpdatableItems[:-1]

        if (UpdatableItems):
            return DatabaseConnector.update_testcase_data(str(id), UpdatableItems, ItemsValues)
        return False

    @classmethod
    def delete_test_case(cls, id):
        return DatabaseConnector.delete_test_case_from_database(int(id))

    @classmethod
    def new_test_version(cls, testcase_id, current_user_name):
        current_test_case = cls.return_testcase_by_id(int(testcase_id))
        latest_version = int(current_test_case['versions'][-1])
        updated_versions_list = ""

        for version in current_test_case['versions']:
            updated_versions_list = updated_versions_list + str(version) + ","

        updated_versions_list = updated_versions_list + str(latest_version + 1)

        return (cls.update_testcase_data(
            int(testcase_id),
            last_updated_by=current_user_name,
            versions=updated_versions_list,
            current_version=latest_version + 1))

    @classmethod
    def delete_current_version(cls, testcase_id):
        current_test_case = cls.return_testcase_by_id(int(testcase_id))

        if (len(current_test_case["versions"]) < 2):
            return False, "The test needs at least one version"

        current_test_case["versions"].remove(
            str(current_test_case["current_version"]))

        version_string = ",".join(current_test_case["versions"])

        if (cls.update_testcase_data(
                int(testcase_id), versions=version_string, current_version=int(current_test_case["versions"][0]))):
            return True, "Test version successfully updated"

        return False, "The version was not possible to be updated"
