
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
    def update_suite_data(cls, id, name=None, project_id=None, description=None, parent_suite_id=None):
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

    @classmethod
    def delete_suite(cls, id):
        return DatabaseConnector.delete_suite_from_database(int(id))

    @classmethod
    def return_suite_by_id(cls, suite_id):
        return DatabaseConnector.return_suite_by_id(int(suite_id))

    @classmethod
    def copy_suite(cls, parent_id, suite_id, current_user, project_id):
        copied_suite = cls.return_suite_by_id(int(suite_id))
        testcases_inside_parent = DatabaseConnector.return_all_suites_names_ids(
            int(project_id),
            int(parent_id)
        )

        if not copied_suite:
            return False

        newName = copied_suite["name"]

        for test in testcases_inside_parent:
            if test["name"] == copied_suite["name"]:
                newName = newName + "(copy)"

        suite_id = cls.add_suite(newName,
                                 copied_suite["description"],
                                 parent_id,
                                 copied_suite["project_id"],
                                 current_user)

        if suite_id:
            return suite_id

        return False
