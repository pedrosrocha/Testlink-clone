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
            session["current_project_id"] = int(_current_project_id)

        _current_project_id = int(session.get('current_project_id'))
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
    data = request.get_json()
    id = data.get('id')
    type = data.get('type')

    if (type == "suite"):
        if TestSuits.delete_suite(id):
            return jsonify(success=True, message="suite deleted successfully")

        return jsonify(success=False, error="Error while deleting the suite")

    # else: type == test
    id = id[2:]
    if TestCases.delete_test_case(id):
        return jsonify(success=True, message="test case deleted successfully")

    return jsonify(success=False, error="Error while deelting the testcase")


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


# @TestSpecification_views.route('/paste_node', methods=['POST'])
# def paste_node():
#    return jsonify(success=True, message="Project updated successfully")


@TestSpecification_views.route('/add_test_case', methods=['POST'])
def add_test_case():
    data = request.get_json()
    node_name = data.get('name')
    parent_id = data.get('parent_id')

    current_user_name = current_user.username
    new_id = TestCases.add_testcase(
        node_name, "", "", "", "draft", "high", parent_id, current_user_name, current_user_name)

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


@TestSpecification_views.route('/paste_test_case', methods=['POST'])
def paste_test_case():
    data = request.get_json()
    test_case_id = data.get('test_id')
    parent_id = data.get('parent_id')

    # removes the "c_" from the string and transforms to integer
    test_case_id = int(test_case_id[2:])
    parent_id = int(parent_id)

    if TestCases.copy_test_case(parent_id, test_case_id, current_user.username):
        return jsonify(success=True, message="Project updated successfully")

    return jsonify(success=False, error="Could not copy test case")


@TestSpecification_views.route('/paste_suite', methods=['POST'])
def paste_suite():
    data = request.get_json()
    suite_id = data.get('suite_id')              # root suite being copied
    parent_id = data.get('parent_id')            # new parent node
    # flat list of all child nodes (suites & tests)
    children = data.get("children")

    # Map old IDs to new ones
    id_map = {}

    # Create the root suite first
    new_root_id = TestSuits.copy_suite(
        parent_id,
        suite_id,
        current_user.username,
        session.get('current_project_id'))

    if not new_root_id:
        return jsonify(success=False, error="Could not create root suite")

    id_map[suite_id] = new_root_id  # link old to new

    for child in children:
        old_parent_id = child["parent"]
        old_id = child["id"]

        new_parent_id = id_map.get(old_parent_id)
        if not new_parent_id:
            return jsonify(success=False, error=f"Missing parent mapping for {old_parent_id}")

        if old_id.startswith('c_'):  # test case
            result = TestCases.copy_test_case(
                new_parent_id,
                old_id[2:],  # remove prefix 'c_'
                current_user.username
            )
            if not result:
                return jsonify(success=False, error=f"Could not create test case {old_id}")

        else:  # suite
            new_suite_id = TestSuits.copy_suite(
                new_parent_id,
                old_id,
                current_user.username,
                session.get('current_project_id'))

            if not new_suite_id:
                return jsonify(success=False, error=f"Could not create suite {old_id}")

            id_map[old_id] = new_suite_id  # store mapping

    return jsonify(success=True, message="Project updated successfully")


@TestSpecification_views.route('/move_suite', methods=['POST'])
def move_suite():
    data = request.get_json()
    suite_id = data.get('node_id')
    parent_id = data.get('parent_id')            # new parent node
    project = int(session.get('current_project_id'))

    if TestSuits.update_testcase_data(suite_id, None, project, None, parent_id):
        return jsonify(success=True, message="Project updated successfully")

    return jsonify(success=False, message="Project not updated")


@TestSpecification_views.route('/move_test', methods=['POST'])
def move_test():
    data = request.get_json()

    test_id = data.get('node_id')
    test_id = test_id[2:]

    parent_id = data.get('parent_id')            # new parent node

    if TestCases.update_testcase_data(test_id, None, parent_id, None, None, None, None, None, None):
        return jsonify(success=True, message="Project updated successfully")

    return jsonify(success=False, message="Project not updated")


@TestSpecification_views.route('/get_testcase_html/<int:testcase_id>', methods=['GET'])
def get_testcase_html(testcase_id):
    test = TestCases.return_testcase_by_id(testcase_id)
    return render_template('partials/testcase_card.html', testcase=test)


@TestSpecification_views.route('/get_suite_html/<int:suite_id>', methods=['GET'])
def get_suite_html(suite_id):
    suite = TestSuits.return_suite_by_id(suite_id)
    return render_template('partials/testsuite_card.html', suite=suite)
