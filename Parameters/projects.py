from .Database.project_database import DatabaseConnector


class projects:

    @classmethod
    def return_all_projects_names(cls):
        return DatabaseConnector.return_all_projects_names()

    @classmethod
    def return_all_projects(cls):
        return DatabaseConnector.return_all_projects()

    @classmethod
    def delete_project(cls, project_id):
        return DatabaseConnector.delete_project_from_database(int(project_id))

    @classmethod
    def add_project(cls, projectName, StartDate, EndDate, Description, username):
        return DatabaseConnector.add_project_to_database(projectName, Description, username, StartDate, EndDate)

    @classmethod
    def return_project_by_name(cls, project_name):
        return DatabaseConnector.return_project_by_name(project_name)

    @classmethod
    def return_project_by_id(cls, project_id):
        return DatabaseConnector.return_project_by_id(int(project_id))

    @classmethod
    def update_project_data(cls, name, description, status, user):
        if status.lower() == 'inactive':
            status = 2
        elif status.lower() == 'archived':
            status = 3
        else:
            status = 1

        if DatabaseConnector.update_project_data(name, description, int(status), user.username):
            return True
        return False
