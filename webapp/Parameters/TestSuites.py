
from .Database.test_suites_database import DatabaseConnector
from ..utils.return_data_model import DatabaseReturnValueModel


class TestSuits():

    @classmethod
    def add_suite(cls, SuiteName, Description, parent_id, project_id, created_by) -> DatabaseReturnValueModel:

        if parent_id:
            parent_id = int(parent_id)

        new_test_id, err = DatabaseConnector.add_suite_to_database(
            SuiteName,
            Description,
            created_by,
            int(project_id),
            parent_id
        )
        if new_test_id:
            return DatabaseReturnValueModel(
                executed=True,
                message=f"suite added.",
                data=new_test_id
            )

        return DatabaseReturnValueModel(
            executed=False,
            message=f"suite was not added.",
            error=err
        )

    @classmethod
    def return_testsuits_from_project(cls, projectID, parentID) -> DatabaseReturnValueModel:
        if parentID:
            suits_list, error = DatabaseConnector.return_all_suites_names_ids(
                int(projectID),
                int(parentID)
            )
            if error:
                return DatabaseReturnValueModel(
                    executed=False,
                    message=f"Not possible to read the list of projects for the id {projectID}",
                    error=error)

            return DatabaseReturnValueModel(
                executed=True,
                message=f"List of projects for the the id read.",
                data=suits_list)

        suits_list, error = DatabaseConnector.return_all_suites_names_ids(
            int(projectID),
            None
        )
        if error:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"Not possible to read the list of projects for the id {projectID}",
                error=error)

        return DatabaseReturnValueModel(
            executed=True,
            message=f"List of projects for the the id read.",
            data=suits_list)

    @classmethod
    def update_suite_data(cls, id, name=None, project_id=None, description=None, parent_suite_id=None) -> DatabaseReturnValueModel:
        UpdatableItems = ""
        ItemsValues = {}

        if name:
            UpdatableItems = UpdatableItems + "name = :name,"
            ItemsValues["name"] = name
        if project_id:
            UpdatableItems = UpdatableItems + "project_id = :project_id,"
            ItemsValues["project_id"] = int(project_id)
        if description:
            UpdatableItems = UpdatableItems + "description = :description,"
            ItemsValues["description"] = description
        if parent_suite_id:
            UpdatableItems = UpdatableItems + "parent_suite_id = :parent_suite_id,"
            ItemsValues["parent_suite_id"] = int(parent_suite_id)

        # removes the "," (comma) from the UpdatableItems top avoid SQL errors
        if (UpdatableItems[-1] == ","):
            UpdatableItems = UpdatableItems[:-1]

        if (UpdatableItems):
            err = DatabaseConnector.update_suite_data(
                str(id),
                UpdatableItems,
                ItemsValues
            )

            if err:
                return DatabaseReturnValueModel(
                    executed=False,
                    message=f"not possible to udpated the suite info for the id {id}",
                    error=err
                )

            return DatabaseReturnValueModel(
                executed=True,
                message=f"the suite {id} info was updated",
            )

        return DatabaseReturnValueModel(
            executed=False,
            message=f"not possible to udpated the suite info for the id {id}",
            error="Nothing to update"
        )

    @classmethod
    def delete_suite(cls, id) -> DatabaseReturnValueModel:
        command_executed, err = DatabaseConnector.delete_suite_from_database(
            int(id))

        if command_executed:
            return DatabaseReturnValueModel(
                executed=True,
                message=f"suite {id} deleted successfuly",
            )

        return DatabaseReturnValueModel(
            executed=False,
            message=f"suite {id} was not possible to be deleted.",
            error=err
        )

    @classmethod
    def return_suite_by_id(cls, suite_id) -> DatabaseReturnValueModel:
        suite, err = DatabaseConnector.return_suite_by_id(int(suite_id))

        if err:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"no suite found for the id {id}",
                error=err
            )

        return DatabaseReturnValueModel(
            executed=True,
            message=f"suite found",
            data=suite
        )

    @classmethod
    def copy_suite(cls, parent_id, suite_id, current_user, project_id) -> DatabaseReturnValueModel:
        copied_suite = cls.return_suite_by_id(int(suite_id)).data
        testcases_inside_parent, err = DatabaseConnector.return_all_suites_names_ids(
            int(project_id),
            int(parent_id)
        )

        if err:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"no suites found inside the folder with the id {parent_id}",
                error=err
            )

        if not copied_suite:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possible to copy the suites.",
                error=err
            )

        newName = copied_suite["name"]

        for test in testcases_inside_parent:
            if test["name"] == copied_suite["name"]:
                newName = newName + "(copy)"

        command = cls.add_suite(
            newName,
            copied_suite["description"],
            parent_id,
            copied_suite["project_id"],
            current_user
        )

        if command.executed:
            return DatabaseReturnValueModel(
                executed=True,
                message="suite created successfuly.",
                data=command.data
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="problem while creating the new suite.",
            error=command.error
        )

    @classmethod
    def update_root_suite_name(cls, project_id, projectName) -> DatabaseReturnValueModel:
        root_suite, err = DatabaseConnector.return_all_suites_names_ids(
            int(project_id),
            None
        )

        if not root_suite:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possible to update the root suite",
                error=err
            )

        command = cls.update_suite_data(root_suite[0].id, projectName)

        if (not command.executed):
            return DatabaseReturnValueModel(
                executed=False,
                message=f"It was not possible to update the root suite",
                error=command.error
            )

        return DatabaseReturnValueModel(
            executed=True,
            message=f"Root name updated successfuly",
        )
