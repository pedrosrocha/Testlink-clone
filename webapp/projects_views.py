from flask import Blueprint, render_template, request, redirect,  session, abort, jsonify, url_for
from flask_login import login_required, current_user
from webapp.utils.roles_controllers import role_required
from webapp.Parameters.projects import projects
from webapp.Parameters.TestSuites import TestSuits


projects_views = Blueprint('projects_views', __name__)


@projects_views.route('/Projects', methods=['GET', 'POST'])
@role_required('admin', 'editor')
@login_required
def ProjectManagement():
    if request.method == 'GET':
        command = projects.return_all_projects()
        if (not command.executed):
            return f"error while reading the projects. error{command.error}"

        return render_template(
            'projects_management.jinja2',
            projects=command.data,
            user=current_user,
            current_project_id=int(
                session.get('current_project_id')
            )
        )

    # if it is a POST
    if current_user.user_level != 'admin':
        abort(403)

    project_id = request.form['id']
    if request.form['action'] == "deletion":

        projects.delete_project(project_id)

        all_projects = projects.return_all_projects().data

        project_id = 1
        if all_projects:
            project_id = all_projects[0]["id"]
        session['current_project_id'] = project_id
        return redirect(url_for('projects_views.ProjectManagement'))

    # if it is not deletion
    return redirect(url_for("auth.MainPage"))


@projects_views.route('/OpenProject/<int:project_id>', methods=['GET', 'POST'])
@role_required('admin', 'editor')
@login_required
def OpenProject(project_id):
    if request.method == 'GET':
        command = projects.return_project_by_id(project_id)
        if (not command.executed):
           # return render_template(
           #    '404.jinja2',
           #    message=f"No project found. error{command.error}",
           #    projects=projects.return_all_projects().data,
           #    current_project_id=int(
           #        session.get('current_project_id')
           #    )
           # ), 404
            abort(404)

        return render_template(
            'open_project.jinja2',
            project=command.data,
            user=current_user,
            projects=projects.return_all_projects().data,
            current_project_id=int(
                session.get('current_project_id')
            )
        )

    # if it is a POST
    if current_user.user_level != 'admin':
        abort(403)

    return render_template(
        '404.jinja2',
        projects=projects.return_all_projects().data,
        current_project_id=int(
            session.get('current_project_id')
        )
    )


@projects_views.route('/EditProject/<int:project_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def EditProject(project_id):
    if request.method == 'GET':
        command = projects.return_project_by_id(project_id)
        if (not command.executed):
            return render_template(
                '404.jinja2',
                message=f"error while reading the projects. error{command.error}",
                projects=projects.return_all_projects().data,
                current_project_id=int(
                    session.get('current_project_id')
                )
            ), 404

        return render_template('edit_project.jinja2', project=command.data, user=current_user, projects=projects.return_all_projects().data)

    # if post
    if current_user.user_level != 'admin':
        return render_template('projects_management.jinja2', projects=projects.return_all_projects().data)

    if request.form['action'] == "editing":
        project_id = request.form["project_id"]
        projectName = request.form['project_name']
        Description = request.form['description']
        Status = request.form['status']

        command = projects.update_project_data(
            project_id,
            projectName,
            Description,
            Status,
            current_user
        )

        # add later: function to update all the project name in the tests and suites
        command = TestSuits.update_root_suite_name(project_id, projectName)

        if not command.executed:
            return render_template('404.jinja2', user=current_user)

        return render_template('projects_management.jinja2', projects=projects.return_all_projects().data, user=current_user)
    return render_template('404.jinja2', user=current_user)


@projects_views.route('/AddProject', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def AddProject():
    if request.method == 'GET':
        return render_template(
            'add_project.jinja2',
            projects=projects.return_all_projects().data,
            current_project_id=int(
                session.get('current_project_id')
            ),
            user=current_user
        )

    # currently, there is not post allowed for non admin users.
    if current_user.user_level != 'admin':
        abort(403)

    # if it is a POST

    projectName = request.form['project_name']
    StartDate = request.form['start_date']
    EndDate = request.form['end_date']
    Description = request.form['description']

    command = projects.add_project(projectName,
                                   StartDate,
                                   EndDate,
                                   Description,
                                   current_user.username
                                   )

    if not command.executed:
        return render_template("error_message.jinja2",
                               error_message="The project name must be unique!",
                               page_url="projects_views.AddProject",
                               page_name="Add project",
                               user=current_user,
                               projects=projects.return_all_projects().data,
                               current_project_id=int(
                                   session.get('current_project_id'))
                               ), 409

    project = projects.return_project_by_name(projectName)
    project_id = 1
    if project.data:
        project_id = project.data["id"]
    session['current_project_id'] = project_id
    TestSuits.add_suite(projectName,
                        f"Root suite for the project {projectName}",
                        None,
                        project.data['id'],
                        current_user.username)

    return redirect(url_for('projects_views.ProjectManagement')), 302


@projects_views.route('/SelectProject', methods=['POST'])
@login_required
def SelectProject():
    project_id = request.json.get('project_id')
    session['current_project_id'] = project_id
    return jsonify(success=True, message="Project updated successfully")
