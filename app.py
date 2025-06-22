from flask import Flask, render_template, request, url_for, redirect, flash, abort
from flask_login import login_manager
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from Parameters.users import testclone_user_list, testclone_user
from utils import url_parser, roles_controllers
from utils.roles_controllers import role_required

app = Flask(__name__)

app.config['SECRET_KEY'] = '3988a0fec3475ef9bc321523e67f29a1f99d12213eadd1c7d12e70a413099a4c'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

Users_manipulation = testclone_user_list(app)


@app.route('/', methods=['GET'])
# The user is directly redirected to the login page if the session is not opened, if the session is opened, the user is redirected to the main page
def index():
    if current_user.is_authenticated:
        return redirect(url_for("MainPage"))
    else:
        return redirect(url_for("login"))


@app.route('/login', methods=['GET', 'POST'])
# Login page route
def login():
    if request.method == 'GET':
        return render_template('login.jinja2')

    # if it is a POST
    username = request.form['username']
    password = request.form['password']

    if Users_manipulation.is_user_valid(username, password):
        user_data = Users_manipulation.return_user_by_username(username)
        user = testclone_user.from_dict(user_data)
        login_user(user)

        next_page = request.args.get('next')

        if not url_parser.is_safe_url(next_page):
            next_page = url_for('MainPage')  # MainPage after login

        return redirect(next_page or url_for('MainPage'))

    flash('Invalid credentials')
    return render_template('login.jinja2')


@login_manager.user_loader
def load_user(user_id):
    user_data = Users_manipulation.get_by_id(user_id)
    if user_data:
        return testclone_user.from_dict(user_data)
    return None


@app.route('/AddUser', methods=['GET', 'POST'])
def AddUser():
    if request.method == 'GET':
        return render_template('add_user.jinja2')

    # if it is a POST
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    next_page = request.args.get('next')

    if not url_parser.is_safe_url(next_page):
        next_page = url_for('MainPage')  # MainPage after login

    Users_manipulation.add_user(username, password, email)
    return redirect(next_page or url_for('login'))


@app.route('/AddUserFromManager', methods=['GET', 'POST'])
def AddUserFromManager():
    if request.method == 'GET':
        return render_template('add_user_from_manager.jinja2')

    # if it is a POST
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    Users_manipulation.add_user(username, password, email)
    return redirect('UsersManagement')


@app.route('/MainPage')
@login_required
def MainPage():
    return render_template('main_page.jinja2', username=current_user.username)


@app.route('/UsersManagement', methods=['GET', 'POST'])
@login_required
def UsersManagement():
    if request.method == 'GET':
        return render_template('users_management.jinja2', users=Users_manipulation.return_users())

    # if it is a POST
    user_id = request.form['id']
    # users_ = Users_manipulation.return_users()
    if request.form['action'] == "deletion":

        Users_manipulation.delete_user(user_id)
        return redirect(url_for('UsersManagement'))

    if request.form['action'] == "reseting":
        return redirect(url_for('ResetUserPassword'))

    if request.form['action'] == "change_level":
        user_id = request.form['id']
        user_level = request.form['new_level']
        if not Users_manipulation.change_user_level(user_id, user_level):
            return render_template("users_management.jinja2", users=Users_manipulation.return_users(), error_message="There must be at least 1 Admin user'.")

        return redirect(url_for('UsersManagement'))

    # currently, there is not post allowed for non admin users.
    if current_user.user_level != 'admin':
        abort(403)

    # In case a non mapped post is sent
    return render_template('404.jinja2')


@app.route('/ResetUserPassword/<string:username>', methods=['GET', 'POST'])
@login_required
def ResetUserPassword(username):
    if request.method == 'GET':
        return render_template('reset_password.jinja2', username=username)

    if request.form['action'] == "reseter":
        password = request.form['newPassword']
        Users_manipulation.change_user_password(username, password)
        return redirect(url_for('UsersManagement'))

    # In case a non mapped post is sent
    return render_template('404.jinja2')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.jinja2'), 403


if __name__ == '__main__':
    app.run(debug=True)
