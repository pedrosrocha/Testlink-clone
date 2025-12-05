import pytest
from flask import Flask, url_for, session, Blueprint
from unittest.mock import Mock, MagicMock, patch
from flask_login import LoginManager, login_user, current_user
from webapp.auth_views import auth
from webapp.Parameters.users import testclone_user
from flask_login import UserMixin


# Mock User class for testing


class TestUser(UserMixin):
    def __init__(self, id, username, user_level):
        self.id = id
        self.username = username
        self.user_level = user_level

    def get_id(self):
        return str(self.id)

# Mock for command results


class MockCommand:
    def __init__(self, executed, error=None, data=None, message=None):
        self.executed = executed
        self.error = error
        self.data = data
        self.message = message


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = Flask(__name__, template_folder='../../webapp/templates')
    app.config['SECRET_KEY'] = 'testing'
    app.config['SERVER_NAME'] = 'localhost'
    app.config['TESTING'] = True

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    projects_bp = Blueprint('projects_views', __name__)
    TestSpecification_views_bp = Blueprint('TestSpecification_views', __name__)
    Users_views_bp = Blueprint('users_views', __name__)

    @projects_bp.route("/ProjectManagement")
    def ProjectManagement():
        return "Project Management"

    @TestSpecification_views_bp.route("/TestSpecification")
    def TestSpecification():
        return "Test specification"

    @Users_views_bp.route("/AddUser")
    def AddUser():
        return "add user"

    @Users_views_bp.route("/UsersManagement")
    def UsersManagement():
        return "Users Management "

    @Users_views_bp.route("/ResetUserPassword")
    def ResetUserPassword():
        return "ResetUserPassword"

    @login_manager.user_loader
    def load_user(user_id):
        if user_id == "1":
            return TestUser(1, "testuser", "admin")
        return None

    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(projects_bp)
    app.register_blueprint(TestSpecification_views_bp)
    app.register_blueprint(Users_views_bp)

    # Mock dependencies
    app.Users_manipulation = MagicMock()

    mock_projects = MagicMock()
    patcher = patch('webapp.auth_views.projects', mock_projects)
    patcher.start()

    yield app

    patcher.stop()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

# Tests for login route


def test_login_get(client):
    """Test GET request to the login page."""
    app = client.application

    with app.app_context():
        response = client.get(url_for('auth.login'))
        assert response.status_code == 200
        assert b'login' in response.data.lower()


def test_login_post_success(client):
    """Test successful login."""
    app = client.application
    app.Users_manipulation.is_user_valid.return_value = MockCommand(
        executed=True)

    user_data = {"id": 1, "username": "testuser", "user_level": "admin"}
    app.Users_manipulation.return_user_by_username.return_value = MockCommand(
        executed=True, data=user_data)

    with app.app_context():
        response = client.post(url_for('auth.login'), data={
            'username': 'testuser',
            'password': 'password'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert response.location == '/MainPage'
        with client.session_transaction() as sess:
            assert sess['_user_id'] == '1'
            assert sess['current_project_id'] is None


def test_login_post_success_with_next(client):
    """Test successful login with a safe next URL."""
    app = client.application
    app.Users_manipulation.is_user_valid.return_value = MockCommand(
        executed=True)
    user_data = {"id": 1, "username": "testuser", "user_level": "admin"}
    app.Users_manipulation.return_user_by_username.return_value = MockCommand(
        executed=True, data=user_data)

    with app.app_context():
        response = client.post(url_for('auth.login', next='/some/path'), data={
            'username': 'testuser',
            'password': 'password'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert response.location == '/some/path'


def test_login_post_success_with_unsafe_next(client):
    """Test successful login with an unsafe next URL."""
    app = client.application
    app.Users_manipulation.is_user_valid.return_value = MockCommand(
        executed=True)
    user_data = {"id": 1, "username": "testuser", "user_level": "admin"}
    app.Users_manipulation.return_user_by_username.return_value = MockCommand(
        executed=True, data=user_data)

    with app.app_context():
        response = client.post(url_for('auth.login', next='http://evil.com'), data={
            'username': 'testuser',
            'password': 'password'
        }, follow_redirects=False)

        assert response.status_code == 302
        # Should redirect to default
        assert response.location == '/MainPage'


def test_login_post_failure(client):
    """Test failed login."""
    app = client.application
    app.Users_manipulation.is_user_valid.return_value = MockCommand(
        executed=False)

    with app.app_context():
        response = client.post(url_for('auth.login'), data={
            'username': 'wronguser',
            'password': 'wrongpassword'
        })

        assert response.status_code == 401
        assert b'Invalid credentials' in response.data
        with client.session_transaction() as sess:
            assert '_user_id' not in sess

# Tests for index routing


def test_index_not_authenticated(client):
    """Test index redirect to login when not authenticated."""
    app = client.application
    with app.app_context():
        response = client.get(url_for('auth.index'))
        assert response.status_code == 302
        assert response.location == '/login'


def test_index_authenticated(client):
    """Test index redirect to MainPage when authenticated."""
    app = client.application
    with app.test_request_context():
        login_user(TestUser(1, "testuser", "admin"))
        response = client.get(url_for('auth.index'), follow_redirects=False)

    assert response.status_code == 302
    assert response.location == '/MainPage'

# Test for logout route


def test_logout(client):
    """Test logout functionality."""
    # Manually log in by setting the session cookie
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    # Verify user is logged in by checking the session
    with client.session_transaction() as sess:
        assert sess['_user_id'] == '1'

    # Perform the logout request
    app = client.application
    with app.app_context():
        response = client.get(url_for('auth.logout'), follow_redirects=False)
        assert response.status_code == 302
        assert response.location == '/login'

    # Verify user is logged out by checking the session
    with client.session_transaction() as sess:
        assert '_user_id' not in sess

# Tests for MainPage route


def test_main_page_unauthenticated(client):
    """Test that MainPage requires login."""
    app = client.application
    with app.app_context():
        response = client.get(url_for('auth.MainPage'))
        assert response.status_code == 302
        assert response.location.startswith('/login')


@patch('webapp.auth_views.projects')
def test_main_page_get(mock_projects, client):
    """Test GET request to the main page."""
    app = client.application
    mock_projects.return_all_projects.return_value = MockCommand(
        executed=True, data=[{'id': 1, 'name': 'Project 1'}]
    )

    # current_user.username

    with app.test_request_context():
        login_user(TestUser(1, "testuser", "admin"))
        response = client.get(url_for('auth.MainPage'))

    assert response.status_code == 200
    assert b'main_page' in response.data.lower()
    assert b'Project 1' in response.data
    with client.session_transaction() as sess:
        assert sess['current_project_id'] == 1


@patch('webapp.auth_views.projects')
def test_main_page_get_with_session_project(mock_projects, client):
    """Test GET request to main page with project_id in session."""
    app = client.application
    mock_projects.return_all_projects.return_value = MockCommand(
        executed=True, data=[{'id': 1, 'name': 'Project 1'}, {
            'id': 2, 'name': 'Project 2'}]
    )

    with app.test_request_context():
        login_user(TestUser(1, "testuser", "admin"))
        with client.session_transaction() as sess:
            sess['current_project_id'] = '2'

        response = client.get(url_for('auth.MainPage'))

    assert response.status_code == 200
    assert b'Project 2' in response.data
    with client.session_transaction() as sess:
        assert sess['current_project_id'] == '2'  # Should not change


@patch('webapp.auth_views.projects')
def test_main_page_get_no_projects(mock_projects, client):
    """Test GET request to main page when there are no projects."""
    app = client.application
    mock_projects.return_all_projects.return_value = MockCommand(
        executed=True, data=[]
    )

    with app.test_request_context():
        login_user(TestUser(1, "testuser", "admin"))
        response = client.get(url_for('auth.MainPage'))

    assert response.status_code == 200
    assert b'main_page' in response.data.lower()
    with client.session_transaction() as sess:
        assert sess['current_project_id'] == 1  # Defaults to 1
