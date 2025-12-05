import pytest
from flask import Flask, url_for, session, Blueprint
from unittest.mock import Mock, MagicMock, patch
from flask_login import LoginManager, login_user
from webapp.users_views import users_views
from webapp.Parameters.users import testclone_user
import pdb
from flask_login import UserMixin

# Mock the return object of the add_user command


class TestUser(UserMixin):
    def __init__(self, id, username, user_level):
        self.id = id
        self.username = username
        self.user_level = user_level

    def get_id(self):
        return str(self.id)


class MockAddUserCommand:
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

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # For tests, just return a dummy admin always
        return TestUser(1, "editor_user", "admin")

    auth_bp = Blueprint('auth', __name__)
    projects_bp = Blueprint('projects_views', __name__)
    TestSpecification_views_bp = Blueprint('TestSpecification_views', __name__)

    @auth_bp.route('/login')
    def login():
        return "Login Page"

    @auth_bp.route('/MainPage')
    def MainPage():
        return "Main Page"

    @auth_bp.route("/logout")
    def logout():
        return "Logged out"

    @projects_bp.route("/ProjectManagement")
    def ProjectManagement():
        return "Project Management"

    @TestSpecification_views_bp.route("/TestSpecification")
    def TestSpecification():
        return "Test specification"

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(TestSpecification_views_bp)
    app.register_blueprint(users_views)

    # Mock the Users_manipulation object that would be on current_app
    app.Users_manipulation = MagicMock()

    # Mock the projects object
    mock_projects = MagicMock()
    mock_projects.return_all_projects.return_value = Mock(data=[])

    # Because the view imports projects directly, we need to patch it
    patcher = patch('webapp.users_views.projects', mock_projects)
    patcher.start()

    yield app

    patcher.stop()


@pytest.fixture
def client(app):
    """A test client for the app."""

    return app.test_client()


@pytest.fixture
def auth_client(client):
    """
    A test client with a pre-populated session.
    Uses the existing `client` fixture.
    """
    with client.session_transaction() as sess:
        sess["current_project_id"] = "1"
        sess["_user_id"] = "1"   # Flask-Login requires this
        sess["_fresh"] = True    # mark login as fresh
    return client


def test_add_user_get(client):
    """Test the GET request for the AddUser view."""
    with client.application.app_context():
        response = client.get(url_for('users_views.AddUser'))
        assert response.status_code == 200
        assert b'Add User' in response.data


def test_add_user_post_success_with_next_page(client):
    """Test a successful POST request to add a new user with a next page."""
    app = client.application
    app.Users_manipulation.add_user.return_value = MockAddUserCommand(
        executed=True)

    with app.app_context():
        response = client.post(url_for('users_views.AddUser', next='/TestSpecification'),
                               data={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert response.location == '/TestSpecification'

        app.Users_manipulation.add_user.assert_called_once_with(
            'testuser',
            'password123',
            'test@example.com'
        )


def test_add_user_post_success_no_next_page(client):
    """Test a successful POST request without a 'next' parameter."""
    app = client.application
    app.Users_manipulation.add_user.return_value = MockAddUserCommand(
        executed=True, message="User added sucessfully")

    with app.app_context():
        response = client.post(url_for('users_views.AddUser'), data={
            'username': 'newuser',
            'password': 'password123',
            'email': 'new@example.com'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert response.location == '/login'
        assert b'Redirecting...' in response.data


def test_add_user_post_failure(client):
    """Test a failed POST request to add a new user."""
    app = client.application
    error_message = "It was not possible to add user."
    app.Users_manipulation.add_user.return_value = MockAddUserCommand(
        executed=False, error=error_message)

    with client.session_transaction() as sess:
        sess['current_project_id'] = '1'

    with app.app_context():
        response = client.post(url_for('users_views.AddUser'), data={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })

        assert response.status_code == 200
        assert error_message.encode() in response.data

        app.Users_manipulation.add_user.assert_called_once_with(
            'testuser',
            'password123',
            'test@example.com'
        )


def test_add_user_post_unsafe_next_url(client):
    """Test POST with an unsafe 'next' URL."""
    app = client.application
    app.Users_manipulation.add_user.return_value = MockAddUserCommand(
        executed=True)

    with app.app_context():
        # A URL outside the host is unsafe
        response = client.post(url_for('users_views.AddUser', next='http://hackersite.com'), data={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })

        assert response.status_code == 302
        # It should redirect to the default main page, not the evil site
        assert response.location == '/MainPage'

        #


def test_add_user_from_manager_get_admin(client):
    app = client.application

    user = TestUser(1, "admin_user", "admin")

    with app.test_request_context():
        login_user(user)

        response = client.get(url_for('users_views.AddUserFromManager'))

        assert response.status_code == 200
        assert b'Add New User' in response.data


def test_add_user_from_manager_get_editor(client):
    app = client.application

    user = TestUser(1, "editor_user", "editor")

    with app.test_request_context():
        login_user(user)

        response = client.get(url_for('users_views.AddUserFromManager'))

        assert response.status_code == 200
        assert b'Add New User' in response.data


def test_add_user_from_manager_get_viewer(client):
    app = client.application

    user = TestUser(1, "viewer_user", "viewer")

    with app.test_request_context():
        login_user(user)

        response = client.get(url_for('users_views.AddUserFromManager'))

        assert response.status_code == 403
        assert b'403 Forbidden' in response.data


def test_add_user_from_manager_post_as_viewer(client):
    app = client.application

    user = TestUser(1, "viewer_user", "viewer")

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.AddUserFromManager'), data={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })

        assert response.status_code == 403
        assert b'403 Forbidden' in response.data

        # pdb.set_trace()


def test_add_user_from_manager_success_post_as_editor(client):
    app = client.application
    app.Users_manipulation.add_user.return_value = MockAddUserCommand(
        executed=True,
        message="User added sucessfully"
    )

    user = TestUser(1, "editor_user", "editor")

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.AddUserFromManager'), data={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })

        assert response.status_code == 302
        assert response.location == '/UsersManagement'
        assert b'Redirecting...' in response.data

        # pdb.set_trace()


def test_add_user_from_manager_success_post_as_admin(client):
    app = client.application
    app.Users_manipulation.add_user.return_value = MockAddUserCommand(
        executed=True,
        message="User added sucessfully"
    )

    user = TestUser(1, "admin_user", "admin")

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.AddUserFromManager'), data={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })

        assert response.status_code == 302
        assert response.location == '/UsersManagement'
        assert b'Redirecting...' in response.data

        # pdb.set_trace()


def test_add_user_from_manager_fail_post_as_editor(client):
    app = client.application
    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    app.Users_manipulation.add_user.return_value = MockAddUserCommand(
        executed=False,
        error="User not added."
    )

    user = TestUser(1, "editor_user", "editor")

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.AddUserFromManager'), data={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })

        assert response.status_code == 400
        assert b'User not added' in response.data
        assert b'Add New User' in response.data


def test_add_user_from_manager_fail_post_as_admin(client):
    app = client.application
    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    app.Users_manipulation.add_user.return_value = MockAddUserCommand(
        executed=False,
        error="User not added."
    )

    user = TestUser(1, "admin_user", "admin")

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.AddUserFromManager'), data={
            'username': 'testuser',
            'password': 'password123',
            'email': 'test@example.com'
        })

        assert response.status_code == 400
        assert b'User not added' in response.data
        assert b'Add New User' in response.data


def test_user_management_get(client):
    app = client.application

    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    user = TestUser(1, "viewer_user", "viewer")
    app.Users_manipulation.return_users.return_value = MockAddUserCommand(
        executed=True, data=[{
            "username": "viewer_user",
            "email": "test@user",
            "user_level": "viewer"}
        ])

    with app.test_request_context():
        login_user(user)

        response = client.get(url_for('users_views.UsersManagement'))

        assert response.status_code == 200
        assert b'User Management System' in response.data
        assert b'Delete' not in response.data

    user = TestUser(1, "editor", "editor")
    app.Users_manipulation.return_users.return_value = MockAddUserCommand(
        executed=True, data=[{
            "username": "test user",
            "email": "test@user",
            "user_level": "viewer"}
        ])

    with app.test_request_context():
        login_user(user)

        response = client.get(url_for('users_views.UsersManagement'))

        assert response.status_code == 200
        assert b'User Management System' in response.data
        assert b'Delete' not in response.data
        assert b'Reset Password' not in response.data

    user = TestUser(1, "admin_admin", "admin")
    app.Users_manipulation.return_users.return_value = MockAddUserCommand(
        executed=True, data=[{
            "username": "test user",
            "email": "test@user",
            "user_level": "viewer"}
        ])

    with app.test_request_context():
        login_user(user)

        response = client.get(url_for('users_views.UsersManagement'))

        assert response.status_code == 200
        assert b'User Management System' in response.data
        assert b'Delete' in response.data
        assert b'Reset Password' in response.data


def test_user_management_delete_user_post_viewer(client):
    app = client.application

    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    user = TestUser(1, "viewer_user", "viewer")
    app.Users_manipulation.delete_user.return_value = MockAddUserCommand(
        executed=False,
        error="it was not possible to delete user."
    )

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.UsersManagement'), data={
            "id": 1,
            "action": "deletion"
        }
        )

        assert response.status_code == 403  # redirect
        assert b'Forbidden' in response.data


def test_user_management_delete_user_post_editor(client):
    app = client.application

    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    user = TestUser(1, "editor", "editor")
    app.Users_manipulation.delete_user.return_value = MockAddUserCommand(
        executed=False,
        error="it was not possible to delete user."
    )

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.UsersManagement'), data={
            "id": 1,
            "action": "deletion"
        }
        )

        assert response.status_code == 403  # redirect
        assert b'Forbidden' in response.data


def test_user_management_delete_user_fail_post_admin(client):
    app = client.application

    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    user = TestUser(1, "admin", "admin")
    app.Users_manipulation.delete_user.return_value = MockAddUserCommand(
        executed=False,
        error="it was not possible to delete user."
    )

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.UsersManagement'), data={
            "id": 1,
            "action": "deletion"
        }
        )

        assert response.status_code == 500
        assert b'it was not possible to delete user.' in response.data


def test_user_management_delete_user_success_post_admin(client):
    app = client.application

    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    user = TestUser(1, "admin", "admin")
    app.Users_manipulation.delete_user.return_value = MockAddUserCommand(
        executed=True,
        message="User deleted successsfully."
    )
    app.Users_manipulation.return_users.return_value = MockAddUserCommand(
        executed=True, data=[{
            "username": "test user",
            "email": "test@user",
            "user_level": "viewer"}
        ])

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.UsersManagement'), data={
            "id": 1,
            "action": "deletion"
        }
        )

        assert response.status_code == 302
        assert b'Redirecting...' in response.data
        assert b'/UsersManagement' in response.data


def test_user_management_reset_pwrd_post_viewer(client):
    app = client.application

    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    user = TestUser(1, "viewer_user", "viewer")

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.UsersManagement'), follow_redirects=False, data={
            "id": 1,
            "action": "reseting"
        }
        )

        assert response.status_code == 403
        assert b'Forbidden' in response.data


def test_user_management_reset_pwrd_post_editor(client):
    app = client.application

    with client.session_transaction() as sess:
        sess['current_project_id'] = "1"
        sess['_user_id'] = "1"               # Flask-Login requires this
        sess['_fresh'] = True                # mark login as fresh

    user = TestUser(1, "editor", "editor")

    with app.test_request_context():
        login_user(user)

        response = client.post(url_for('users_views.UsersManagement'), follow_redirects=False, data={
            "id": 1,
            "action": "reseting"
        }
        )

        assert response.status_code == 403
        assert b'Forbidden' in response.data


def test_user_management_reset_pwrd_post_admin(auth_client):
    app = auth_client.application

    user = TestUser(1, "admin", "admin")

    with app.test_request_context():
        login_user(user)

        response = auth_client.post(url_for('users_views.UsersManagement'), follow_redirects=False, data={
            "id": 1,
            "action": "reseting"
        }
        )

        assert response.status_code == 302
        # this test returns error due to the redirect that is hadled by the htmls instead of the backend


def test_user_management_get_fail(auth_client):
    """Test GET UsersManagement when the user list command fails."""
    app = auth_client.application
    app.Users_manipulation.return_users.return_value = MockAddUserCommand(
        executed=False,
        error="Database connection failed."
    )

    admin_user = TestUser(1, "admin_user", "admin")

    with app.test_request_context():
        login_user(admin_user)
        response = auth_client.get(url_for('users_views.UsersManagement'))

        assert response.status_code == 200
        assert b"Database connection failed." in response.data
        assert b"Users management" in response.data


def test_user_management_change_level_post_admin_success(auth_client):
    """Test successful user level change by an admin."""
    app = auth_client.application
    app.Users_manipulation.change_user_level.return_value = MockAddUserCommand(
        executed=True)

    admin_user = TestUser(1, "admin_user", "admin")

    with app.test_request_context():
        login_user(admin_user)
        response = auth_client.post(url_for('users_views.UsersManagement'), data={
            "id": "2",
            "new_level": "editor",
            "action": "change_level"
        })

        assert response.status_code == 302
        assert response.location == '/UsersManagement'
        app.Users_manipulation.change_user_level.assert_called_once_with(
            "2", "editor")


def test_user_management_change_level_post_admin_fail(auth_client):
    """Test failed user level change by an admin (e.g., last admin)."""
    app = auth_client.application
    app.Users_manipulation.change_user_level.return_value = MockAddUserCommand(
        executed=False, error="not possible to change user level")

    admin_user = TestUser(1, "admin_user", "admin")

    with app.test_request_context():
        login_user(admin_user)
        response = auth_client.post(url_for('users_views.UsersManagement'), data={
            "id": "1",
            "new_level": "editor",
            "action": "change_level"
        })

        assert response.status_code == 200
        assert b"not possible to change user level" in response.data


def test_user_management_change_level_post_editor(client):
    """Test that an editor cannot change a user's level."""
    app = client.application
    editor_user = TestUser(2, "editor_user", "editor")

    with app.test_request_context():
        login_user(editor_user)
        response = client.post(url_for('users_views.UsersManagement'), data={
            "id": "1",
            "new_level": "admin",
            "action": "change_level"
        })

        assert response.status_code == 403
        assert b'Forbidden' in response.data


def test_user_management_unmapped_action_post_admin(client):
    """Test POST with an unmapped action to UsersManagement as admin."""
    app = client.application
    admin_user = TestUser(1, "admin_user", "admin")

    with app.test_request_context():
        login_user(admin_user)
        response = client.post(url_for('users_views.UsersManagement'), data={
            "id": "1",
            "action": "unknown_action"
        })

        assert response.status_code == 404
        assert b'404 - Page not found' in response.data


def test_reset_user_password_get_admin(auth_client):
    """Test GET ResetUserPassword as an admin."""
    app = auth_client.application
    admin_user = TestUser(1, "admin_user", "admin")
    target_username = "user_to_reset"

    with app.test_request_context():
        login_user(admin_user)
        response = auth_client.get(
            url_for('users_views.ResetUserPassword', username=target_username))

        assert response.status_code == 200
        assert b'Reset user_to_reset' in response.data
        assert target_username.encode() in response.data


def test_reset_user_password_get_editor(auth_client):
    """Test GET ResetUserPassword as an editor."""
    app = auth_client.application
    editor_user = TestUser(2, "editor_user", "editor")
    target_username = "user_to_reset"

    with app.test_request_context():
        login_user(editor_user)
        response = auth_client.get(
            url_for('users_views.ResetUserPassword', username=target_username))

        assert response.status_code == 200


def test_reset_user_password_get_viewer(auth_client):
    """Test GET ResetUserPassword as an editor (should be forbidden)."""
    app = auth_client.application
    editor_user = TestUser(2, "editor_user", "editor")
    target_username = "user_to_reset"

    with app.test_request_context():
        login_user(editor_user)
        response = auth_client.get(
            url_for('users_views.ResetUserPassword', username=target_username))

        assert response.status_code == 200


def test_reset_user_password_post_admin_success(client):
    """Test successful password reset by an admin."""
    app = client.application
    app.Users_manipulation.change_user_password.return_value = MockAddUserCommand(
        executed=True)

    admin_user = TestUser(1, "admin_user", "admin")
    target_username = "user_to_reset"

    with app.test_request_context():
        login_user(admin_user)
        response = client.post(url_for('users_views.ResetUserPassword', username=target_username), data={
            "newPassword": "new_secure_password_123",
            "action": "reseter"
        })

        assert response.status_code == 302
        assert response.location == '/UsersManagement'
        app.Users_manipulation.change_user_password.assert_called_once_with(
            target_username, "new_secure_password_123")


def test_reset_user_password_post_editor(client):
    """Test POST to ResetUserPassword as an editor (should be forbidden)."""
    app = client.application
    editor_user = TestUser(2, "editor_user", "editor")
    target_username = "user_to_reset"

    with app.test_request_context():
        login_user(editor_user)
        response = client.post(url_for('users_views.ResetUserPassword', username=target_username), data={
            "newPassword": "new_secure_password_123",
            "action": "reseter"
        })

        assert response.status_code == 403


def test_reset_user_password_unmapped_action_post_admin(auth_client):
    """Test POST with an unmapped action to ResetUserPassword as admin."""
    app = auth_client.application
    admin_user = TestUser(1, "admin_user", "admin")
    target_username = "user_to_reset"

    with app.test_request_context():
        login_user(admin_user)
        response = auth_client.post(url_for('users_views.UsersManagement', username=target_username), data={
            "action": "unknown_action",
            "id": 1
        })

        assert response.status_code == 404
        assert b'404 - Page not found' in response.data
