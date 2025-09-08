from flask import Blueprint, render_template, request, url_for, redirect,  session, abort, current_app
from flask_login import login_required, current_user
from webapp.Parameters.projects import projects
from webapp.Parameters.users import testclone_user_list
from webapp.utils import url_parser
from webapp.utils.roles_controllers import role_required


users_views = Blueprint('users_views', __name__)


@users_views.route('/AddUser', methods=['GET', 'POST'])
def AddUser():
    if request.method == 'GET':
        return render_template('add_user.jinja2')

    # if it is a POST
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    next_page = request.args.get('next')

    if not url_parser.is_safe_url(next_page):
        next_page = url_for('auth.MainPage')  # MainPage after login

    if not current_app.Users_manipulation.add_user(username, password, email):
        return render_template('add_user.jinja2',
                               error_message=f"The user {username} already exists'.",
                               projects=projects.return_all_projects(),
                               current_project_id=int(session.get('current_project_id')))

    return redirect(next_page or url_for('auth.login'))


@users_views.route('/AddUserFromManager', methods=['GET', 'POST'])
@login_required
@role_required('editor', 'admin')
def AddUserFromManager():
    if request.method == 'GET':
        return render_template('add_user_from_manager.jinja2')

    # if it is a POST
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    if not current_app.Users_manipulation.add_user(username, password, email):
        return render_template('add_user.jinja2',
                               error_message=f"The user {username} already exists'.",
                               user=current_user, projects=projects.return_all_projects(),
                               current_project_id=int(session.get('current_project_id')))

    return redirect(url_for('users_views.UsersManagement'))


@users_views.route('/UsersManagement', methods=['GET', 'POST'])
@login_required
def UsersManagement():
    if request.method == 'GET':
        return render_template('users_management.jinja2',
                               users=current_app.Users_manipulation.return_users(),
                               user=current_user,
                               projects=projects.return_all_projects().data,
                               current_project_id=int(session.get('current_project_id')))

    # if it is a POST
    user_id = request.form['id']
    if request.form['action'] == "deletion":

        if not current_app.Users_manipulation.delete_user(user_id):
            return render_template("error_message.jinja2",
                                   error_message="There must be at least one admin user!",
                                   page_url="users_views.UsersManagement",
                                   page_name="Users management",
                                   user=current_user,
                                   projects=projects.return_all_projects(),
                                   current_project_id=int(session.get('current_project_id')))
        return redirect(url_for('users_views.UsersManagement'))

    if request.form['action'] == "reseting":
        return redirect(url_for('users_views.ResetUserPassword'))

    if request.form['action'] == "change_level":
        user_id = request.form['id']
        user_level = request.form['new_level']
        if not current_app.Users_manipulation.change_user_level(user_id, user_level):
            return render_template("error_message.jinja2",
                                   error_message="There must be at least one admin user!",
                                   page_url="users_views.UsersManagement",
                                   page_name="Users management",
                                   user=current_user,
                                   projects=projects.return_all_projects(),
                                   current_project_id=int(session.get('current_project_id')))
            # return render_template("users_management.jinja2", users=current_app.Users_manipulation.return_users(), error_message="There must be at least 1 Admin user.")

        return redirect(url_for('users_views.UsersManagement'))

    # currently, there is not post allowed for non admin users.
    if current_user.user_level != 'admin':
        abort(403)

    # In case a non mapped post is sent
    return render_template('404.jinja2')


@users_views.route('/ResetUserPassword/<string:username>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def ResetUserPassword(username):
    if request.method == 'GET':
        return render_template('reset_password.jinja2',
                               username=username,
                               projects=projects.return_all_projects(),
                               current_project_id=int(session.get('current_project_id')))

    if current_user.user_level != 'admin':
        abort(403)
    if request.form['action'] == "reseter":
        password = request.form['newPassword']
        current_app.Users_manipulation.change_user_password(username, password)
        return redirect(url_for('users_views.UsersManagement'))

    # In case a non mapped post is sent
    return render_template('404.jinja2',
                           projects=projects.return_all_projects(),
                           current_project_id=int(session.get('current_project_id')))
