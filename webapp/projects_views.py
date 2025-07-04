from flask import Blueprint, render_template, request, redirect,   session, abort, jsonify, current_app
from flask_login import login_required, current_user
from webapp.utils.roles_controllers import role_required
from webapp.Parameters.projects import projects


projects_views = Blueprint('projects_views', __name__)


@projects_views.route('/Projects', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def ProjectManagement():
    if request.method == 'GET':
        return render_template('projects_management.jinja2',
                               projects=projects.return_all_projects(),
                               user=current_user,
                               current_project_id=int(session.get('current_project_id')))

    # if it is a POST
    if current_user.user_level != 'admin':
        abort(403)

    project_id = request.form['id']
    if request.form['action'] == "deletion":

        projects.delete_project(project_id)
        return render_template('projects_management.jinja2',
                               projects=projects.return_all_projects(),
                               user=current_user,
                               current_project_id=int(session.get('current_project_id')))

    # if it is deletion

    return "UiiiiHooo"


@projects_views.route('/OpenProject/<int:project_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def OpenProject(project_id):
    if request.method == 'GET':
        project_ = projects.return_project_by_id(project_id)
        return render_template('open_project.jinja2',
                               project=project_,
                               user=current_user,
                               projects=projects.return_all_projects(),
                               current_project_id=int(session.get('current_project_id')))

    # if it is a POST
    if current_user.user_level != 'admin':
        abort(403)
    return render_template('404.jinja2',
                           projects=projects.return_all_projects(),
                           current_project_id=int(session.get('current_project_id')))


@projects_views.route('/EditProject/<int:project_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def EditProject(project_id):
    if request.method == 'GET':
        project_ = projects.return_project_by_id(project_id)
        return render_template('edit_project.jinja2', project=project_, user=current_user, projects=projects.return_all_projects())
    # if post

    if current_user.user_level != 'admin':
        return render_template('projects_management.jinja2', projects=projects.return_all_projects())

    if request.form['action'] == "editing":
        projectName = request.form['project_name']
        Description = request.form['description']
        Status = request.form['status']

        projects.update_project_data(
            projectName, Description, Status, current_user)
        # add later: function to update all the project name in the tests and suites
        return render_template('projects_management.jinja2', projects=projects.return_all_projects(), user=current_user)
    return render_template('404.jinja2', user=current_user)


@projects_views.route('/AddProject', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def AddProject():
    if request.method == 'GET':
        return render_template('add_project.jinja2',
                               projects=projects.return_all_projects(),
                               current_project_id=int(session.get('current_project_id')))

    # currently, there is not post allowed for non admin users.
    if current_user.user_level != 'admin':
        abort(403)

    # if it is a POST

    projectName = request.form['project_name']
    StartDate = request.form['start_date']
    EndDate = request.form['end_date']
    Description = request.form['description']

    projects.add_project(projectName,
                         StartDate,
                         EndDate,
                         Description,
                         current_user.username)

    return redirect('projects_views.Projects',
                    user=current_user,
                    projects=projects.return_all_projects(),
                    current_project_id=int(session.get('current_project_id')))


@projects_views.route('/SelectProject', methods=['POST'])
@login_required
def SelectProject():
    # print("Data as JSON:", request.get_json())  # print json request

    project_id = request.json.get('project_id')
    # print("project_id: ", project_id)
    session['current_project_id'] = project_id
    return jsonify(success=True, message="Project updated successfully")
