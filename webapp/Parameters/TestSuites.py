
from .Database.test_suites_database import DatabaseConnector


class TestSuits():
    @classmethod
    def return_testSuits(cls, Projectid):
        pass

    @classmethod
    def add_suite(cls, SuiteName, Description, parent_id, project_id, created_by):
        if parent_id:
            return DatabaseConnector.add_suite_to_database(
                SuiteName, Description, created_by, int(project_id), int(parent_id))

        else:
            return DatabaseConnector.add_suite_to_database(
                SuiteName, Description, created_by, int(project_id), None)

    @classmethod
    def return_testsuits_from_project(cls, projectID, parentID):
        if parentID:
            return DatabaseConnector.return_all_suites_names_ids(int(projectID), int(parentID))

        return DatabaseConnector.return_all_suites_names_ids(int(projectID), None)

    @classmethod
    def update_testcase_data(cls, id, name=None, project_id=None, description=None, parent_suite_id=None):
        UpdatableItems = ""
        ItemsValues = {}

        if name:
            UpdatableItems = UpdatableItems + "name = :name,"
            ItemsValues["name"] = name
        if project_id:
            UpdatableItems = UpdatableItems + "project_id = :project_id,"
            ItemsValues["project_id"] = project_id
        if description:
            UpdatableItems = UpdatableItems + "description = :description,"
            ItemsValues["description"] = description
        if parent_suite_id:
            UpdatableItems = UpdatableItems + "parent_suite_id = :parent_suite_id,"
            ItemsValues["parent_suite_id"] = parent_suite_id

        # removes the "," (comma) from the UpdatableItems top avoid SQL errors
        if (UpdatableItems[-1] == ","):
            UpdatableItems = UpdatableItems[:-1]

        if (UpdatableItems):
            return DatabaseConnector.update_suite_data(str(id), UpdatableItems, ItemsValues)
        return False
