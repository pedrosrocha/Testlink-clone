from flask import Blueprint, render_template, request, url_for, redirect, flash,  session, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from webapp.Parameters.users import testclone_user_list, testclone_user
from webapp.utils import url_parser
from webapp.utils.roles_controllers import role_required
from webapp.Parameters.projects import projects
from webapp.Parameters.TestSuites import TestSuits
from webapp.Parameters.TestCases import TestCases


TestSpecification_views = Blueprint('TestSpecification_views', __name__)


@TestSpecification_views.route('/TestSpecification', methods=['GET', 'POST'])
@login_required
def TestSpecification():
    if request.method == 'GET':
        if (not session.get('current_project_id')):
            _current_project_id = int(projects.return_oldest_project()["id"])
            session["current_project_id"] = _current_project_id

        _current_project_id = session.get('current_project_id')
        return render_template('test_specification.jinja2',
                               projects=projects.return_all_projects(),
                               current_project_id=_current_project_id,
                               user=current_user)


@TestSpecification_views.route('/get_test_tree_root')
def get_test_tree_root():

    _current_project_id = session.get('current_project_id')
    suites = TestSuits.return_testsuits_from_project(_current_project_id, None)

    return jsonify([
        {
            'id': suite["id"],
            'text': suite["name"],
            'type': "suite",
            'children': True  # To enable lazy loading
        } for suite in suites
    ])


@TestSpecification_views.route('/get_test_tree_children')
def get_test_tree_children():
    node_id = request.args.get('id')  # Node id returned from jstree

    children = []

    if node_id:
        suite_id = int(node_id)

        _current_project_id = session.get('current_project_id')

        suites = TestSuits.return_testsuits_from_project(
            _current_project_id,
            suite_id
        )

        for suite in suites:
            children.append({
                'id': suite["id"],
                'text': suite["name"],
                'type': "suite",
                'children': True  # This is what makes the jstrre lazy loading possible
            })

        cases = TestCases.return_testcases_from_project(suite_id)

        for case in cases:
            children.append({
                'id': f'c_{case["id"]}',
                'text': case["name"],
                'type': "test",
                'children': False  # Leaf node
            })

    return jsonify(children)


@TestSpecification_views.route('/delete_node', methods=['POST'])
def delete_node():
    return jsonify(success=True, message="Project updated successfully")


@TestSpecification_views.route('/rename_node', methods=['POST'])
def rename_node():
    data = request.get_json()
    id = data.get('id')
    new_name = data.get('new_name')
    type = data.get('type')

    if (type == "suite"):
        if TestSuits.update_testcase_data(id, name=new_name):
            return jsonify(success=True, message="Project updated successfully")

        return jsonify(success=False, error="Error while renaming the suite")

    # else: type == test
    current_user_name = current_user.username
    id = id[2:]
    if TestCases.update_testcase_data(id, name=new_name, last_updated_by=current_user_name):

        return jsonify(success=True, message="Project updated successfully")

    return jsonify(success=False, error="Error while renaming the testcase")


@TestSpecification_views.route('/paste_node', methods=['POST'])
def paste_node():
    return jsonify(success=True, message="Project updated successfully")


@TestSpecification_views.route('/add_test_case', methods=['POST'])
def add_test_case():
    data = request.get_json()
    node_name = data.get('name')
    parent_id = data.get('parent_id')

    current_user_id = current_user.username
    new_id = TestCases.add_testcase(
        node_name, "", "", "", "draft", "high", parent_id, current_user_id, current_user_id)

    return jsonify(success=True, message="Project updated successfully", name=node_name, id=new_id)


@TestSpecification_views.route('/add_suite', methods=['POST'])
def add_suite():
    data = request.get_json()
    node_name = data.get('name')
    parent_id = data.get('parent_id')

    _current_project_id = session.get('current_project_id')
    current_user.username
    new_id = TestSuits.add_suite(node_name,
                                 "",
                                 parent_id,
                                 _current_project_id,
                                 current_user.username)
    return jsonify(success=True, message="Project updated successfully", name=node_name, id=new_id)
