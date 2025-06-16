from flask import Flask, render_template, request, url_for, redirect, flash
from flask_login import login_manager
from Parameters.users import testclone_user
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from Parameters.users import testclone_user_list
from utils import url_parser

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

    # return the user informartion necessary for the flask to work
    user = testclone_user(username, password)

    if Users_manipulation.is_user_valid(username, password):
        login_user(user)

        next_page = request.args.get('next')

        if not url_parser.is_safe_url(next_page):
            next_page = url_for('MainPage')  # MainPage after login

        return redirect(next_page or url_for('MainPage'))

    flash('Invalid credentials')
    return render_template('login.jinja2')


@login_manager.user_loader
def load_user(username):
    user_data = Users_manipulation.return_user_by_username(username)
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
    users_ = Users_manipulation.return_users()
    if request.form['action'] == "deletion":
        Users_manipulation.delete_user(user_id)
        return render_template('users_management.jinja2', users=users_)

    # render_template('reset_user_password.jinja2', username=users_[user_id]["username"])
    return "in production"


# @app.route('/ResetUserPassword', methods=['GET', 'POST'])
# @login_required
# def ResetUserPassword():
#    if request.method == 'GET':
#        return render_template('reset_user_password.jinja2')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
