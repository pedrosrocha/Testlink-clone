
import pytest
from flask import Flask, url_for, Blueprint
from unittest.mock import patch
from flask_login import LoginManager, login_user
from webapp.projects_views import projects_views
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

    @login_manager.user_loader
    def load_user(user_id):
        if user_id == "1":
            return TestUser(1, "admin", "admin")
        if user_id == "2":
            return TestUser(2, "editor", "editor")
        if user_id == "3":
            return TestUser(3, "viewer", "viewer")
        return None

    auth_bp = Blueprint('auth', __name__)
    TestSpecification_views_bp = Blueprint('TestSpecification_views', __name__)
    Users_views_bp = Blueprint('users_views', __name__)

    @auth_bp.route('/login')
    def login():
        return "Login Page"

    @auth_bp.route('/MainPage')
    def MainPage():
        return "Main Page"

    @auth_bp.route("/logout")
    def logout():
        return "Logged out"

    @TestSpecification_views_bp.route("/TestSpecification")
    def TestSpecification():
        return "Test specification"

    @Users_views_bp.route("/UsersManagement")
    def UsersManagement():
        return "Users Management "

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_views)
    app.register_blueprint(TestSpecification_views_bp)
    app.register_blueprint(Users_views_bp)

    with patch('webapp.projects_views.projects') as mock_projects:
        mock_projects.return_all_projects.return_value = MockCommand(
            executed=True, data=[{'id': 1, 'name': 'Project 1'}])
        yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    with client.session_transaction() as sess:
        sess["current_project_id"] = "1"
        sess["_user_id"] = "1"
        sess["_fresh"] = True
    return client

# Tests for ProjectManagement route


def test_project_management_get_as_admin(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(url_for('projects_views.ProjectManagement'))
        assert response.status_code == 200
        assert b'Project Management System' in response.data


def test_project_management_get_as_editor(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(2, "editor", "editor"))
        response = auth_client.get(url_for('projects_views.ProjectManagement'))
        assert response.status_code == 200
        assert b'Project Management System' in response.data


def test_project_management_get_as_viewer(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(3, "viewer", "viewer"))
        response = auth_client.get(url_for('projects_views.ProjectManagement'))
        assert response.status_code == 403


@patch('webapp.projects_views.projects')
def test_project_management_post_delete_as_admin(mock_projects, auth_client):
    app = auth_client.application
    mock_projects.delete_project.return_value = MockCommand(executed=True)
    mock_projects.return_all_projects.return_value = MockCommand(
        executed=True, data=[])

    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('projects_views.ProjectManagement'), data={
                                    'id': '1', 'action': 'deletion'
                                    }
                                    )
        assert response.status_code == 302
        assert response.location == '/Projects'
        with auth_client.session_transaction() as sess:
            assert sess['current_project_id'] == 1


def test_project_management_post_delete_as_editor(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(2, "editor", "editor"))
        response = auth_client.post(url_for('projects_views.ProjectManagement'), data={
                                    'id': '1', 'action': 'deletion'})
        assert response.status_code == 403


def test_project_management_post_delete_as_viewer(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(3, "viewer", "viewer"))
        response = auth_client.post(url_for('projects_views.ProjectManagement'), data={
                                    'id': '1', 'action': 'deletion'})
        assert response.status_code == 403

# Tests for AddProject route


def test_add_project_get_as_admin(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(url_for('projects_views.AddProject'))
        assert response.status_code == 200
        assert b'Add New Project' in response.data


def test_add_project_get_as_editor(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(2, "editor", "editor"))
        response = auth_client.get(url_for('projects_views.AddProject'))
        assert response.status_code == 403


@patch('webapp.projects_views.projects')
@patch('webapp.projects_views.TestSuits')
def test_add_project_post_as_admin(mock_test_suits, mock_projects, auth_client):
    app = auth_client.application
    mock_projects.add_project.return_value = MockCommand(executed=True)
    mock_projects.return_project_by_name.return_value = MockCommand(
        executed=True, data={'id': 2, 'name': 'New Project'})
    mock_test_suits.add_suite.return_value = MockCommand(executed=True)

    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('projects_views.AddProject'), data={
            'project_name': 'New Project',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'description': 'A new project'
        })
        assert response.status_code == 302
        assert response.location == '/Projects'
        with auth_client.session_transaction() as sess:
            assert sess['current_project_id'] == 2


@patch('webapp.projects_views.projects')
def test_add_project_post_as_admin_fail(mock_projects, auth_client):
    app = auth_client.application
    mock_projects.add_project.return_value = MockCommand(
        executed=False, error="The project name must be unique")

    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('projects_views.AddProject'), data={
            'project_name': 'New Project',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
            'description': 'A new project'
        })
        assert response.status_code == 409
        assert b'The project name must be unique!' in response.data

# Tests for EditProject route


@patch('webapp.projects_views.projects')
def test_edit_project_get_as_admin(mock_projects, auth_client):
    app = auth_client.application
    mock_projects.return_project_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'name': 'Project 1'})
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('projects_views.EditProject', project_id=1))
        assert response.status_code == 200
        assert b'Edit Project' in response.data


def test_edit_project_get_as_editor(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(2, "editor", "editor"))
        response = auth_client.get(
            url_for('projects_views.EditProject', project_id=1))
        assert response.status_code == 403


@patch('webapp.projects_views.projects')
@patch('webapp.projects_views.TestSuits')
def test_edit_project_post_as_admin(mock_test_suits, mock_projects, auth_client):
    app = auth_client.application
    mock_projects.update_project_data.return_value = MockCommand(executed=True)
    mock_test_suits.update_root_suite_name.return_value = MockCommand(
        executed=True)
    mock_projects.return_all_projects.return_value = MockCommand(
        executed=True, data=[{'id': 1, 'name': 'Updated Project'}])

    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('projects_views.EditProject', project_id=1), data={
            'action': 'editing',
            'project_id': 1,
            'project_name': 'Updated Project',
            'description': 'Updated description',
            'status': 'active'
        })
        assert response.status_code == 200
        assert b'Project Management System' in response.data

# Tests for OpenProject route


@patch('webapp.projects_views.projects')
def test_open_project_get_as_admin(mock_projects, auth_client):
    app = auth_client.application
    mock_projects.return_project_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'name': 'Project 1'})
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('projects_views.OpenProject', project_id=1))
        assert response.status_code == 200
        assert b'Project Information' in response.data

# Tests for SelectProject route


def test_select_project_post(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(
            url_for('projects_views.SelectProject'), json={'project_id': 2})
        assert response.status_code == 200
        assert response.json['success'] is True
        with auth_client.session_transaction() as sess:
            assert sess['current_project_id'] == 2
