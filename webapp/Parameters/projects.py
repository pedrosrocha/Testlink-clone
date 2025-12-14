from .Database.project_database import DatabaseConnector
from ..utils.return_data_model import DatabaseReturnValueModel
from cachetools import cached, TTLCache

# cache used for the project list
projects_cache = TTLCache(maxsize=128, ttl=3600)


class projects:

    @classmethod
    @cached(cache=projects_cache)
    def return_all_projects_names(cls) -> DatabaseReturnValueModel:
        """
        Retrieves the names of all projects from the database.
        """
        result, database_error = DatabaseConnector.return_all_projects_names()

        if result is not None:
            return DatabaseReturnValueModel(
                executed=True,
                message="Project names read successfully.",
                data=result
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="An error occurred while reading project names.",
            error=database_error
        )

    @classmethod
    @cached(cache=projects_cache)
    def return_all_projects(cls) -> DatabaseReturnValueModel:
        """
        Retrieves all data for all projects from the database.
        """
        result, database_error = DatabaseConnector.return_all_projects()

        if result is not None:
            return DatabaseReturnValueModel(
                executed=True,
                message="All projects read successfully.",
                data=result
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="An error occurred while reading all projects.",
            error=database_error
        )

    @classmethod
    def delete_project(cls, project_id: int) -> DatabaseReturnValueModel:
        """
        Deletes a project from the database by its ID.
        """
        was_deleted, database_error = DatabaseConnector.delete_project_from_database(
            int(project_id))

        if was_deleted:

            # if the project was successfully deleted, then the cache is cleared to enable the program to read the updated data
            projects_cache.clear()

            return DatabaseReturnValueModel(
                executed=True,
                message=f"Project with ID {project_id} deleted successfully."
            )

        return DatabaseReturnValueModel(
            executed=False,
            message=f"Failed to delete project with ID {project_id}.",
            error=database_error
        )

    @classmethod
    def add_project(cls, projectName: str, StartDate: str, EndDate: str, Description: str, username: str) -> DatabaseReturnValueModel:
        """
        Adds a new project to the database after checking for duplicate names.
        """
        # Check for duplicates (case-insensitive)
        existing_projects_result = cls.return_all_projects_names()

        if not existing_projects_result.executed:
            return DatabaseReturnValueModel(
                executed=False,
                message="It was not possible to read all the projects names.",
                error=existing_projects_result.error
            )

        for project in existing_projects_result.data:
            if project['name'].lower() == projectName.lower():
                return DatabaseReturnValueModel(
                    executed=False,
                    message=f"Not possible to create a project with the name: '{projectName}'.",
                    error=f"A project with the name '{projectName}' already exists."
                )

        # Add project to database
        was_added, database_error = DatabaseConnector.add_project_to_database(
            projectName,
            Description,
            username,
            StartDate,
            EndDate
        )

        if was_added:
            # if the project was successfully added, then the cache is cleared to enable the program to read the updated data
            projects_cache.clear()

            return DatabaseReturnValueModel(
                executed=True,
                message=f"Project '{projectName}' added successfully."
            )
        else:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"An error occurred while adding the project '{projectName}' to the database.",
                error=database_error
            )

    @classmethod
    @cached(cache=projects_cache)
    def return_project_by_name(cls, project_name: str) -> DatabaseReturnValueModel:
        """
        Retrieves a single project from the database by its name.
        """
        if not project_name:
            return DatabaseReturnValueModel(executed=False, message="Project name cannot be empty.")

        project, database_error = DatabaseConnector.return_project_by_name(
            project_name)

        if project:
            return DatabaseReturnValueModel(
                executed=True,
                message=f"Project '{project_name}' found.",
                data=project
            )
        else:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"Project with name '{project_name}' not found.",
                error=database_error
            )

    @classmethod
    @cached(cache=projects_cache)
    def return_project_by_id(cls, project_id: int) -> DatabaseReturnValueModel:
        """
        Retrieves a single project from the database by its ID.
        """
        project_data_as_row, database_error = DatabaseConnector.return_project_by_id(
            int(project_id))

        if project_data_as_row:
            project_data = [dict(project_data_as_row)]

            return DatabaseReturnValueModel(
                executed=True,
                message=f"Project with ID {project_id} found.",
                data=project_data[0]
            )
        else:
            return DatabaseReturnValueModel(
                executed=False,
                message=f"Project with ID {project_id} not found.",
                error=database_error
            )

    @classmethod
    def update_project_data(cls, project_id: str, name: str, description: str, status: str, user) -> DatabaseReturnValueModel:
        """
        Updates a project's status and description.
        """
        status_map = {'inactive': 2, 'archived': 3, 'active': 1}
        status_code = status_map.get(status.lower(), 1)

        was_updated, database_error = DatabaseConnector.update_project_data(
            int(project_id),
            name,
            description,
            status_code,
            user.username
        )

        if was_updated:
            # if the project was successfully updated, then the cache is cleared to enable the program to read the updated data

            projects_cache.clear()
            return DatabaseReturnValueModel(
                executed=True,
                message=f"Project '{name}' updated successfully."
            )

        return DatabaseReturnValueModel(
            executed=False,
            message=f"Failed to update project '{name}'.",
            error=database_error
        )

    @classmethod
    @cached(cache=projects_cache)
    def return_oldest_project(cls) -> DatabaseReturnValueModel:
        """
        Retrieves the oldest project from the database (based on creation date).
        """
        first_project, database_error = DatabaseConnector.return_first_project()

        if first_project:
            return DatabaseReturnValueModel(
                executed=True,
                message="Oldest project found.",
                data=first_project,
            )

        return DatabaseReturnValueModel(
            executed=False,
            message="No projects found in the database.",
            error=database_error
        )
