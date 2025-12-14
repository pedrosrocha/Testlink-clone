
from .Database.test_cases_database import DatabaseConnector
from datetime import datetime
from ..utils.return_data_model import DatabaseReturnValueModel


class TestCases():
    @classmethod
    def return_testcase_by_id(cls, testcase_id) -> DatabaseReturnValueModel:
        testDict, err = DatabaseConnector.return_testcase_by_id(
            int(testcase_id))

        if err:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"the test case {testcase_id} was not found.",
                error=err
            )

        testDict = dict(testDict)

        versions_list = testDict["versions"].split(',')
        testDict['versions'] = versions_list

        if (testDict):
            return DatabaseReturnValueModel(
                executed=True,
                message=f"the test case {testcase_id} was found.",
                data=testDict
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="Invalid test case dictionary.",
            error=f"the test dictionary was empty or invalid:\n {testDict}"
        )

    @classmethod
    def copy_test_case(cls, parent_id, testcase_id, current_user) -> DatabaseReturnValueModel:
        copied_testcase = cls.return_testcase_by_id(int(testcase_id)).data
        if not copied_testcase:
            return DatabaseReturnValueModel(
                executed=False,
                message="It was not possible to copy the test cases. ",
                error="no test case was copied.")

        testcases_inside_parent = cls.return_testcases_from_project(
            int(parent_id))

        if not testcases_inside_parent.executed:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possibel to read all the testcase names inside the parent suite {parent_id} ",
                error=testcases_inside_parent.error
            )

        newName = copied_testcase["name"]

        for test in testcases_inside_parent.data:
            if test["name"] == copied_testcase["name"]:
                current_datetime = datetime.now()
                newName = current_datetime.ctime() + " : " + newName
                break

        new_id = cls.add_testcase(
            newName,
            copied_testcase["description"],
            copied_testcase["preconditions"],
            copied_testcase["expected_result"],
            copied_testcase["status"],
            copied_testcase["priority"],
            parent_id,
            current_user,
            current_user
        )
        return DatabaseReturnValueModel(
            executed=True,
            message="test case successfully copied. ",
            data=new_id.data
        )

    @classmethod
    def add_testcase(cls, test_name, Description, precondition, expected_result, status, priority, suite_id, created_by, last_updated_by) -> DatabaseReturnValueModel:
        if (not status):
            status = "draft"

        if (not priority):
            priority = "high"

        test_case_id, err = DatabaseConnector.add_test_case_to_database(
            int(suite_id),
            test_name,
            Description,
            precondition,
            expected_result,
            priority,
            status,
            created_by,
            last_updated_by
        )
        if err:
            return DatabaseReturnValueModel(
                executed=False,
                message="It was not possible to add the test case.",
                error=err
            )
        return DatabaseReturnValueModel(
            executed=True,
            message="Test case added sucessfuly",
            data=test_case_id
        )

    @classmethod
    def return_testcases_from_project(cls, parentID) -> DatabaseReturnValueModel:
        test_cases, err = DatabaseConnector.return_all_cases_names_ids(
            int(parentID))
        if err:
            return DatabaseReturnValueModel(
                executed=False,
                message="It was not possibel to read all the testcase names. ",
                error=err
            )

        return DatabaseReturnValueModel(
            executed=True,
            message="test cases read. ",
            data=test_cases
        )

    @classmethod
    def update_testcase_data(cls, id, name=None, suite_id=None, description=None, precondition=None, expected_result=None, priority=None, status=None, last_updated_by=None, versions=None, current_version=None) -> DatabaseReturnValueModel:
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

        ItemsValues["id"] = int(id)

        if (UpdatableItems):
            err = DatabaseConnector.update_testcase_data(
                UpdatableItems,
                ItemsValues
            )
            if err:
                return DatabaseReturnValueModel(
                    executed=False,
                    message=f"It was not possible to update the test {id}.",
                    error=err
                )
        return DatabaseReturnValueModel(
            executed=True,
            message=f"Test {id} was updated successfuly.",
        )

    @classmethod
    def delete_test_case(cls, id) -> DatabaseReturnValueModel:
        err = DatabaseConnector.delete_test_case_from_database(int(id))
        if err:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possible to delete the test case {id}. ",
                error=err
            )

        return DatabaseReturnValueModel(
            executed=True,
            message=f"Test case {id} deleted successfuly. "
        )

    @classmethod
    def new_test_version(cls, testcase_id, current_user_name) -> DatabaseReturnValueModel:
        current_test_case = cls.return_testcase_by_id(int(testcase_id)).data
        latest_version = int(current_test_case['versions'][-1])
        updated_versions_list = ""

        for version in current_test_case['versions']:
            updated_versions_list = updated_versions_list + str(version) + ","

        updated_versions_list = updated_versions_list + str(latest_version + 1)

        update_testcase = cls.update_testcase_data(
            int(testcase_id),
            last_updated_by=current_user_name,
            versions=updated_versions_list,
            current_version=latest_version + 1
        )

        if update_testcase.executed:
            return DatabaseReturnValueModel(
                executed=True,
                message="new version added succesfuly",
            )
        return DatabaseReturnValueModel(
            executed=False,
            error=update_testcase.error,
        )

    @classmethod
    def delete_current_version(cls, testcase_id) -> DatabaseReturnValueModel:
        current_test_case = cls.return_testcase_by_id(int(testcase_id)).data

        if (len(current_test_case["versions"]) < 2):
            return False, "The test needs at least one version"

        current_test_case["versions"].remove(
            str(current_test_case["current_version"]))

        version_string = ",".join(current_test_case["versions"])

        update_command = cls.update_testcase_data(
            int(testcase_id),
            versions=version_string,
            current_version=int(current_test_case["versions"][0])
        )

        if (update_command.executed):
            return DatabaseReturnValueModel(
                executed=True,
                message="current version deleted successfuly"
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="current version was not deleted",
            error=update_command.error
        )
