
import pytest
from flask import Flask, url_for, Blueprint
from unittest.mock import patch
from flask_login import LoginManager, login_user
from webapp.TestSpecification_views import TestSpecification_views
from flask_login import UserMixin

# Mock User class for testing


class TestUser(UserMixin):
    def __init__(self, id, username, user_level):
        self.id = id
        self.username = username
        self.user_level = user_level
        self.editing_steps = False

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
    Users_views_bp = Blueprint('users_views', __name__)
    projects_bp = Blueprint('projects_views', __name__)

    @auth_bp.route('/login')
    def login():
        return "Login Page"

    @auth_bp.route('/MainPage')
    def MainPage():
        return "Main Page"

    @auth_bp.route("/logout")
    def logout():
        return "Logged out"

    @Users_views_bp.route("/UsersManagement")
    def UsersManagement():
        return "Users Management "

    @projects_bp.route("/ProjectManagement")
    def ProjectManagement():
        return "Project Management"

    app.register_blueprint(auth_bp)
    app.register_blueprint(TestSpecification_views)
    app.register_blueprint(Users_views_bp)
    app.register_blueprint(projects_bp)

    with patch('webapp.TestSpecification_views.projects') as mock_projects, patch('webapp.TestSpecification_views.TestSuits') as mock_test_suits, patch('webapp.TestSpecification_views.TestCases') as mock_test_cases:

        mock_projects.return_all_projects.return_value = MockCommand(
            executed=True, data=[{'id': 1, 'name': 'Project 1'}])
        mock_projects.return_oldest_project.return_value = MockCommand(
            executed=True, data={'id': 1, 'name': 'Project 1'})
        mock_test_suits.return_testsuits_from_project.return_value = MockCommand(
            executed=True, data=[{'id': 1, 'name': 'Suite 1'}])
        mock_test_cases.return_testcases_from_project.return_value = MockCommand(
            executed=True, data=[{'id': 1, 'name': 'Case 1'}])

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

# Tests for TestSpecification route


def test_test_specification_get(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.TestSpecification'))
        assert response.status_code == 200
        assert b'Test Specification' in response.data

    with app.test_request_context():
        login_user(TestUser(1, "editor", "editor"))
        response = auth_client.get(
            url_for('TestSpecification_views.TestSpecification'))
        assert response.status_code == 200
        assert b'Test Specification' in response.data

    with app.test_request_context():
        login_user(TestUser(1, "viewer", "viewer"))
        response = auth_client.get(
            url_for('TestSpecification_views.TestSpecification'))
        assert response.status_code == 200
        assert b'Test Specification' in response.data

# Tests for get_test_tree_root route


def test_get_test_tree_root(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.get_test_tree_root'))
        assert response.status_code == 200
        assert response.json[0]['text'] == 'Suite 1'

# Tests for get_test_tree_children route


def test_get_test_tree_children(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.get_test_tree_children', id=1))
        assert response.status_code == 200
        assert len(response.json) == 2
        assert response.json[0]['text'] == 'Suite 1'
        assert response.json[1]['text'] == '1:Case 1'

# Tests for delete_node route


@patch('webapp.TestSpecification_views.TestSuits')
def test_delete_node_suite_as_admin(mock_test_suits, auth_client):
    app = auth_client.application
    mock_test_suits.delete_suite.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(
            url_for('TestSpecification_views.delete_node'), json={'id': 1, 'type': 'suite'})
        assert response.status_code == 200
        assert response.json['success'] is True


@patch('webapp.TestSpecification_views.TestCases')
def test_delete_node_test_as_admin(mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.delete_test_case.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.delete_node'), json={
                                    'id': 'c_1', 'type': 'test'})
        assert response.status_code == 200
        assert response.json['success'] is True


def test_delete_node_as_viewer(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(3, "viewer", "viewer"))
        response = auth_client.post(
            url_for('TestSpecification_views.delete_node'), json={'id': 1, 'type': 'suite'})
        assert response.status_code == 403

# Tests for rename_node route


@patch('webapp.TestSpecification_views.TestSuits')
def test_rename_node_suite_as_admin(mock_test_suits, auth_client):
    app = auth_client.application
    mock_test_suits.update_suite_data.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.rename_node'), json={
                                    'id': 1, 'new_name': 'New Name', 'type': 'suite'})
        assert response.status_code == 200
        assert response.json['success'] is True


@patch('webapp.TestSpecification_views.TestCases')
def test_rename_node_test_as_admin(mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.update_testcase_data.return_value = MockCommand(
        executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.rename_node'), json={
                                    'id': 'c_1', 'new_name': 'New Name', 'type': 'test'})
        assert response.status_code == 200
        assert response.json['success'] is True


def test_rename_node_as_viewer(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(3, "viewer", "viewer"))
        response = auth_client.post(url_for('TestSpecification_views.rename_node'), json={
                                    'id': 1, 'new_name': 'New Name', 'type': 'suite'})
        assert response.status_code == 403

# Tests for add_test_case route


@patch('webapp.TestSpecification_views.TestCases')
def test_add_test_case_as_admin(mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.add_testcase.return_value = MockCommand(
        executed=True, data=2)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.add_test_case'), json={
            'name': 'New Test Case',
            'parent_id': 1,
            'description': 'A new test case',
            'precondition': 'None',
            'expected_results': 'It works',
            'status': 'Draft',
            'priority': 'Medium'
        })
        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['id'] == 2


def test_add_test_case_as_viewer(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(3, "viewer", "viewer"))
        response = auth_client.post(url_for('TestSpecification_views.add_test_case'), json={
            'name': 'New Test Case',
            'parent_id': 1
        })
        assert response.status_code == 403

# Tests for add_suite route


@patch('webapp.TestSpecification_views.TestSuits')
def test_add_suite_as_admin(mock_test_suits, auth_client):
    app = auth_client.application
    mock_test_suits.add_suite.return_value = MockCommand(executed=True, data=2)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.add_suite'), json={
            'name': 'New Suite',
            'parent_id': 1,
            'description': 'A new suite'
        })
        assert response.status_code == 201
        assert response.json['success'] is True
        assert response.json['id'] == 2


def test_add_suite_as_viewer(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(3, "viewer", "viewer"))
        response = auth_client.post(url_for('TestSpecification_views.add_suite'), json={
            'name': 'New Suite',
            'parent_id': 1
        })
        assert response.status_code == 403

# Tests for paste_test_case route


@patch('webapp.TestSpecification_views.TestCases')
@patch('webapp.TestSpecification_views.TestSteps')
def test_paste_test_case_as_admin(mock_test_steps, mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.copy_test_case.return_value = MockCommand(
        executed=True, data=2, message="steps copied successfuly. ")
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={"current_version": 1})
    mock_test_steps.copy_steps.return_value = MockCommand(
        executed=True, message="steps copied successfuly. ")
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.paste_test_case'), json={
            'test_id': 'c_1',
            'parent_id': 2
        })
        assert response.status_code == 201
        assert response.json['success'] is True

# Tests for paste_suite route


@patch('webapp.TestSpecification_views.TestSuits')
@patch('webapp.TestSpecification_views.TestCases')
@patch('webapp.TestSpecification_views.TestSteps')
def test_paste_suite_as_admin(mock_test_steps, mock_test_cases, mock_test_suits, auth_client):
    app = auth_client.application
    mock_test_suits.copy_suite.return_value = MockCommand(
        executed=True, data=2)
    mock_test_cases.copy_test_case.return_value = MockCommand(
        executed=True, data=3)
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={"current_version": 1})
    mock_test_steps.copy_steps.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.paste_suite'), json={
            'suite_id': 1,
            'parent_id': 2,
            'children': [{'id': 'c_1', 'parent': 1}]
        })
        assert response.status_code == 201
        assert response.json['success'] is True

# Tests for move_suite route


@patch('webapp.TestSpecification_views.TestSuits')
def test_move_suite_as_admin(mock_test_suits, auth_client):
    app = auth_client.application
    mock_test_suits.update_suite_data.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.move_suite'), json={
            'node_id': 1,
            'parent_id': 2
        })
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for move_test route


@patch('webapp.TestSpecification_views.TestCases')
def test_move_test_as_admin(mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.update_testcase_data.return_value = MockCommand(
        executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.move_test'), json={
            'node_id': 'c_1',
            'parent_id': 2
        })
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for get_testcase_html route


@patch('webapp.TestSpecification_views.TestCases')
@patch('webapp.TestSpecification_views.TestSteps')
def test_get_testcase_html(mock_test_steps, mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'name': 'Test Case 1', 'current_version': 1})
    mock_test_steps.return_steps_from_test_cases.return_value = MockCommand(
        executed=True, data=[])
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.get_testcase_html', testcase_id=1))
        assert response.status_code == 200
        assert b'Test Case 1' in response.data

# Tests for get_suite_html route


@patch('webapp.TestSpecification_views.TestSuits')
def test_get_suite_html(mock_test_suits, auth_client):
    app = auth_client.application
    mock_test_suits.return_suite_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'name': 'Suite 1'})
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.get_suite_html', suite_id=1))
        assert response.status_code == 200
        assert b'Suite 1' in response.data

# Tests for new_test_case_form route


def test_new_test_case_form(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.new_test_case_form'))
        assert response.status_code == 200
        assert b'Add New Test Case' in response.data

# Tests for edit_suite route


@patch('webapp.TestSpecification_views.TestSuits')
def test_edit_suite(mock_test_suits, auth_client):
    app = auth_client.application
    mock_test_suits.return_suite_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'name': 'Suite 1'})
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(
            url_for('TestSpecification_views.edit_suite'), json={'id': 1})
        assert response.status_code == 200
        assert b'Edit Test Suite' in response.data

# Tests for edit_test_case route


@patch('webapp.TestSpecification_views.TestCases')
def test_edit_test_case(mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'name': 'Test Case 1'})
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(
            url_for('TestSpecification_views.edit_test_case'), json={'id': 'c_1'})
        assert response.status_code == 200
        assert b'Edit Test Case' in response.data

# Tests for new_suite_form route


def test_new_suite_form(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.new_suite_form'))
        assert response.status_code == 200
        assert b'Add New Test Suite' in response.data

# Tests for update_test_case route


@patch('webapp.TestSpecification_views.TestCases')
def test_update_test_case(mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.update_testcase_data.return_value = MockCommand(
        executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.update_test_case'), json={
            'id': 'c_1',
            'name': 'Updated Name'
        })
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for update_suite route


@patch('webapp.TestSpecification_views.TestSuits')
def test_update_suite(mock_test_suits, auth_client):
    app = auth_client.application
    mock_test_suits.update_suite_data.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.update_suite'), json={
            'id': 1,
            'name': 'Updated Name'
        })
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for new_test_case_version route


@patch('webapp.TestSpecification_views.TestCases')
@patch('webapp.TestSpecification_views.TestSteps')
def test_new_test_case_version(mock_test_steps, mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={'current_version': 1})
    mock_test_cases.new_test_version.return_value = MockCommand(executed=True)
    mock_test_steps.copy_steps_new_version.return_value = MockCommand(
        executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(
            url_for('TestSpecification_views.new_test_case_version'), json={'id': 'c_1'})
        assert response.status_code == 201
        assert response.json['success'] is True

# Tests for update_test_case_version route


@patch('webapp.TestSpecification_views.TestCases')
def test_update_test_case_version(mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.update_testcase_data.return_value = MockCommand(
        executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.update_test_case_version'), json={
            'id': 1,
            'version': 2
        })
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for delete_testcase_version route


@patch('webapp.TestSpecification_views.TestCases')
def test_delete_testcase_version(mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.delete_current_version.return_value = MockCommand(
        executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(
            url_for('TestSpecification_views.delete_testcase_version'), json={'id': 'c_1'})
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for save_step_data route


@patch('webapp.TestSpecification_views.TestSteps')
def test_save_step_data(mock_test_steps, auth_client):
    app = auth_client.application
    mock_test_steps.update_step_info.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.save_step_data'), json={
            'id': 1,
            'actions_data': 'New Action',
            'results_data': 'New Result'
        })
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for new_step route


@patch('webapp.TestSpecification_views.TestCases')
@patch('webapp.TestSpecification_views.TestSteps')
def test_new_step(mock_test_steps, mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'current_version': 1})
    mock_test_steps.create_new_step.return_value = MockCommand(
        executed=True, message="step created successfuly.")
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.new_step'), json={
            'test_id': 1,
            'actions_data': 'New Action',
            'results_data': 'New Result',
            'previous_step_id': 0
        })
        assert response.status_code == 201
        assert response.json['success'] is True

# Tests for delete_step route


@patch('webapp.TestSpecification_views.TestCases')
@patch('webapp.TestSpecification_views.TestSteps')
def test_delete_step(mock_test_steps, mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={'current_version': 1})
    mock_test_steps.delete_step.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.delete_step'), json={
            'step_id': 1,
            'test_id': 1
        })
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for set_edit_mode route


def test_set_edit_mode(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(
            url_for('TestSpecification_views.set_edit_mode'), json={'edit_mode': True})
        assert response.status_code == 200
        assert response.json['success'] is True
        with auth_client.session_transaction() as sess:
            assert sess['editing_steps'] is True

# Tests for get_edit_mode route


def test_get_edit_mode(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.get_edit_mode'))
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for reorder_steps route


@patch('webapp.TestSpecification_views.TestSteps')
def test_reorder_steps(mock_test_steps, auth_client):
    app = auth_client.application
    mock_test_steps.reorder_steps_position.return_value = MockCommand(
        executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.reorder_steps'), json={
            'id': 1,
            'steps': [1, 2, 3]
        })
        assert response.status_code == 200
        assert response.json['success'] is True

# Tests for copy_step route


@patch('webapp.TestSpecification_views.TestCases')
@patch('webapp.TestSpecification_views.TestSteps')
def test_copy_step(mock_test_steps, mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_steps.return_step_by_id.return_value = MockCommand(
        executed=True, data={'step_action': 'Action', 'expected_value': 'Result'})
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'current_version': 1})
    mock_test_steps.create_new_step.return_value = MockCommand(executed=True)
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.copy_step'), json={
            'copied_step_id': 1,
            'test_id': 1,
            'clicked_step_id': 2
        })
        assert response.status_code == 201
        assert response.json['success'] is True

# Tests for compare_test_versions route


@patch('webapp.TestSpecification_views.TestCases')
@patch('webapp.TestSpecification_views.TestSteps')
def test_compare_test_versions(mock_test_steps, mock_test_cases, auth_client):
    app = auth_client.application
    mock_test_cases.return_testcase_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'current_version': 1, 'versions': [1, 2]})
    mock_test_steps.return_steps_from_test_cases.side_effect = [
        MockCommand(executed=True, data=[]),
        MockCommand(executed=True, data=[])
    ]
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.post(url_for('TestSpecification_views.compare_test_versions'), json={
            'id': 'c_1',
            'left_compare': 1,
            'right_compare': 2
        })
        assert response.status_code == 200
        assert b'Test case:' in response.data

# Tests for get_user_level route


def test_get_user_level(auth_client):
    app = auth_client.application
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.get_user_level'))
        assert response.status_code == 200
        assert response.json['user_level'] == 'admin'

# Tests for get_step route


@patch('webapp.TestSpecification_views.TestSteps')
def test_get_step(mock_test_steps, auth_client):
    app = auth_client.application
    mock_test_steps.return_step_by_id.return_value = MockCommand(
        executed=True, data={'id': 1, 'step_action': 'Action'})
    with app.test_request_context():
        login_user(TestUser(1, "admin", "admin"))
        response = auth_client.get(
            url_for('TestSpecification_views.get_step', step=1))
        assert response.status_code == 200
        assert response.json['success'] is True
        assert response.json['step']['id'] == 1
