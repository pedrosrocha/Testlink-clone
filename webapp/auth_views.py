from flask import Blueprint, render_template, request, url_for, redirect, flash,  session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from webapp.Parameters.users import testclone_user_list, testclone_user
from webapp.Parameters.projects import projects
from webapp.utils import url_parser

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
# Login page route
def login():
    if request.method == 'GET':
        return render_template('login.jinja2', user=current_user)

    # if it is a POST
    username = request.form['username']
    password = request.form['password']

    if current_app.Users_manipulation.is_user_valid(username, password):
        user = current_app.Users_manipulation.return_user_by_username(
            username)
        login_user(testclone_user.from_dict(user.data))

        next_page = request.args.get('next')

        if not url_parser.is_safe_url(next_page):
            next_page = url_for('auth.MainPage')  # MainPage after login

        # Initializes the project id as null
        session['current_project_id'] = None

        return redirect(next_page or url_for('auth.MainPage'))

    flash('Invalid credentials')
    return render_template('login.jinja2', user=None), 401


@auth.route('/', methods=['GET'])
# The user is directly redirected to the login page if the session is not opened, if the session is opened, the user is redirected to the main page
def index():
    if current_user.is_authenticated:
        return redirect(url_for("auth.MainPage"))
    return redirect(url_for("auth.login"))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/MainPage')
@login_required
def MainPage():
    command = projects.return_all_projects()
    _current_id = 0

    if session.get('current_project_id'):
        _current_id = int(session.get('current_project_id'))

    # this was added to handle a system without project
    current_project_id = command.data[0]['id'] if command.data else 1

    if not _current_id:
        session['current_project_id'] = int(current_project_id)
    return render_template('main_page.jinja2',
                           username=current_user.username,
                           projects=command.data,
                           current_project_id=int(
                               session.get('current_project_id')
                           ),
                           user=current_user)
