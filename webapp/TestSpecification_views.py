from flask import Blueprint, render_template, request, url_for, redirect, flash,  session, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from webapp.Parameters.users import testclone_user_list, testclone_user
from webapp.utils import url_parser
from webapp.utils.roles_controllers import role_required
from webapp.Parameters.projects import projects
from webapp.Parameters.TestSuites import TestSuits
from webapp.Parameters.TestCases import TestCases
from webapp.Parameters.TestSteps import TestSteps

TestSpecification_views = Blueprint('TestSpecification_views', __name__)


@TestSpecification_views.route('/TestSpecification', methods=['GET', 'POST'])
@login_required
def TestSpecification():
    if request.method == 'GET':
        if (not session.get('current_project_id')):
            _current_project_id = int(projects.return_oldest_project()["id"])
            session["current_project_id"] = int(_current_project_id)

        if (not session.get('editing_steps')):
            session["editing_steps"] = False

        _current_project_id = int(session.get('current_project_id'))
        return render_template(
            'test_specification.jinja2',
            projects=projects.return_all_projects().data,
            current_project_id=_current_project_id,
            user=current_user
        )


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
@role_required('admin', 'editor')
@login_required
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
@role_required('admin', 'editor')
@login_required
def rename_node():
    data = request.get_json()
    id = data.get('id')
    new_name = data.get('new_name')
    type = data.get('type')

    if (type == "suite"):
        if TestSuits.update_suite_data(id, name=new_name):
            return jsonify(success=True, message="Project updated successfully")

        return jsonify(success=False, error="Error while renaming the suite")

    # else: type == test
    current_user_name = current_user.username
    id = id[2:]
    if TestCases.update_testcase_data(id, name=new_name, last_updated_by=current_user_name):

        return jsonify(success=True, message="Project updated successfully")

    return jsonify(success=False, error="Error while renaming the testcase")


@TestSpecification_views.route('/add_test_case', methods=['POST'])
@role_required('admin', 'editor')
@login_required
def add_test_case():
    data = request.get_json()
    node_name = data.get('name')
    parent_id = data.get('parent_id')
    description = data.get('description') if data.get('description') else ""
    precondition = data.get('precondition') if data.get('precondition') else ""
    expected_results = data.get('expected_results') if data.get(
        'expected_results') else ""
    status = data.get('status')
    priority = data.get('priority')

    current_user_name = current_user.username
    new_id = TestCases.add_testcase(
        node_name, description, precondition, expected_results, status, priority, parent_id, current_user_name, current_user_name)

    return jsonify(success=True, message="Project updated successfully", name=node_name, id=new_id)


@TestSpecification_views.route('/add_suite', methods=['POST'])
@role_required('admin', 'editor')
@login_required
def add_suite():
    data = request.get_json()
    node_name = data.get('name')
    parent_id = data.get('parent_id')
    description = data.get('description') if data.get('description') else ""

    _current_project_id = session.get('current_project_id')
    current_user.username
    new_id = TestSuits.add_suite(node_name,
                                 description,
                                 parent_id,
                                 _current_project_id,
                                 current_user.username)
    return jsonify(success=True, message="Project updated successfully", name=node_name, id=new_id)


@TestSpecification_views.route('/paste_test_case', methods=['POST'])
@role_required('admin', 'editor')
@login_required
def paste_test_case():
    data = request.get_json()
    test_case_id = data.get('test_id')
    parent_id = data.get('parent_id')

    # removes the "c_" from the string and transforms to integer
    test_case_id = int(test_case_id[2:])
    parent_id = int(parent_id)

    new_id = TestCases.copy_test_case(
        parent_id,
        test_case_id,
        current_user.username
    )
    if new_id:

        current_version_to_copy = TestCases.return_testcase_by_id(test_case_id)[
            "current_version"
        ]

        TestSteps.copy_steps(
            test_case_id,
            current_version_to_copy,
            new_id
        )

        return jsonify(success=True, message="Project updated successfully")

    return jsonify(success=False, error="Could not copy test case")


@TestSpecification_views.route('/paste_suite', methods=['POST'])
@role_required('admin', 'editor')
@login_required
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
            new_id = TestCases.copy_test_case(
                new_parent_id,
                old_id[2:],  # remove prefix 'c_'
                current_user.username
            )
            if not new_id:
                return jsonify(success=False, error=f"Could not create test case {old_id}")

            current_version_to_copy = TestCases.return_testcase_by_id(old_id[2:])[
                "current_version"
            ]
            TestSteps.copy_steps(
                old_id[2:],  # remove prefix 'c_')
                current_version_to_copy,
                new_id
            )

        else:  # suite
            new_suite_id = TestSuits.copy_suite(
                new_parent_id,
                old_id,
                current_user.username,
                session.get('current_project_id')
            )

            if not new_suite_id:
                return jsonify(success=False, error=f"Could not create suite {old_id}")

            id_map[old_id] = new_suite_id  # store mapping

    return jsonify(success=True, message="Project updated successfully")


@TestSpecification_views.route('/move_suite', methods=['POST'])
@role_required('admin', 'editor')
@login_required
def move_suite():
    data = request.get_json()
    suite_id = data.get('node_id')
    parent_id = data.get('parent_id')            # new parent node
    project = int(session.get('current_project_id'))

    if TestSuits.update_suite_data(suite_id, None, project, None, parent_id):
        return jsonify(success=True, message="Project updated successfully")

    return jsonify(success=False, error="Project not updated")


@TestSpecification_views.route('/move_test', methods=['POST'])
@role_required('admin', 'editor')
@login_required
def move_test():
    data = request.get_json()

    test_id = data.get('node_id')
    test_id = test_id[2:]

    parent_id = data.get('parent_id')            # new parent node

    test_case_data = TestCases.update_testcase_data(
        test_id, None, parent_id, None, None, None, None, None, None)

    if test_case_data:
        return jsonify(success=True, message="Project updated successfully")

    return jsonify(success=False, error="Project not updated")


@TestSpecification_views.route('/get_testcase_html/<int:testcase_id>', methods=['GET'])
def get_testcase_html(testcase_id):
    _testcase = TestCases.return_testcase_by_id(testcase_id)

    if not _testcase:
        return f"test case id = {testcase_id} not found"

    teststeps = TestSteps.return_steps_from_test_cases(
        _testcase["id"],
        _testcase["current_version"])

    if not teststeps[0]:
        return f"test case steps id = {testcase_id} not found"

    return render_template(
        'partials/testcase_card.jinja2',
        testcase=_testcase, test_steps=teststeps[1],
        editing_steps=session.get('editing_steps'),
        user=current_user
    )


@TestSpecification_views.route('/get_suite_html/<int:suite_id>', methods=['GET'])
def get_suite_html(suite_id):
    suite = TestSuits.return_suite_by_id(suite_id)
    return render_template(
        'partials/testsuite_card.jinja2',
        suite=suite,
        user=current_user
    )


@TestSpecification_views.route("/new_test_case_form", methods=['GET'])
@role_required('admin', 'editor')
@login_required
def new_test_case_form():
    return render_template('partials/add_new_test_case.html')


@TestSpecification_views.route("/edit_suite", methods=['POST'])
@role_required('admin', 'editor')
@login_required
def edit_suite():
    data = request.get_json()
    suite_id = data.get('id')

    _suite = TestSuits.return_suite_by_id(suite_id)
    return render_template('partials/edit_suite.jinja2', suite=_suite)


@TestSpecification_views.route("/edit_test_case", methods=['POST'])
@role_required('admin', 'editor')
@login_required
def edit_test_case():
    data = request.get_json()
    test_id = data.get('id')

    # removes the "c_" from the string and transforms to integer
    test_id = int(test_id[2:])

    current_test_case = TestCases.return_testcase_by_id(test_id)
    return render_template('partials/edit_test_case.jinja2', testcase=current_test_case)


@TestSpecification_views.route("/new_suite_form", methods=['GET'])
@role_required('admin', 'editor')
@login_required
def new_suite_form():
    return render_template('partials/add_new_suite.html')


@TestSpecification_views.route("/update_test_case", methods=['POST'])
@role_required('admin', 'editor')
@login_required
def update_test_case():
    data = request.get_json()
    id = data.get('id')[2:]
    name = data.get('name')
    description = data.get('description')
    preconditions = data.get('preconditions')
    expected_results = data.get('expected_results')
    priority = data.get('priority')
    status = data.get('status')

    if (TestCases.update_testcase_data(id,
                                       name,
                                       False,
                                       description,
                                       preconditions,
                                       expected_results,
                                       priority,
                                       status,
                                       current_user.username)):
        return jsonify(success=True, message="Test updated successfuly")

    return jsonify(success=False, error="It was not possible to update the test information")


@TestSpecification_views.route("/update_suite", methods=['POST'])
@role_required('admin', 'editor')
@login_required
def update_suite():
    data = request.get_json()
    id = data.get('id')
    name = data.get('name')
    description = data.get('description')

    if (TestSuits.update_suite_data(id, name, False, description, None)):
        return jsonify(success=True, message="Suite updated successfuly")

    return jsonify(success=False, error="It was not possible to update the suite information")


@TestSpecification_views.route("/new_test_case_version", methods=['POST'])
@role_required('admin', 'editor')
@login_required
def new_test_case_version():
    data = request.get_json()
    id = data.get('id')[2:]

    testcase_previous_version = TestCases.return_testcase_by_id(id)[
        "current_version"]

    if (TestCases.new_test_version(id, current_user.username)):
        testcase_new_version = TestCases.return_testcase_by_id(id)[
            "current_version"
        ]

        TestSteps.copy_steps_new_version(
            id,
            testcase_previous_version,
            testcase_new_version
        )

        return jsonify(success=True, message="Test version created  successfuly")

    return jsonify(success=False, error="It was not possible to create the new version")


@TestSpecification_views.route("/update_test_case_version", methods=['POST'])
@login_required
def update_test_case_version():
    data = request.get_json()
    id = data.get('id')
    version = data.get("version")

    if (TestCases.update_testcase_data(id, current_version=version)):
        return jsonify(success=True, message="Test version created  successfuly")

    return jsonify(success=False, error="It was not possible to create the new version")


@TestSpecification_views.route("/delete_testcase_version", methods=['POST'])
@role_required('admin', 'editor')
@login_required
def delete_testcase_version():
    data = request.get_json()
    id = data.get('id')[2:]

    command_execution = TestCases.delete_current_version(id)
    if (command_execution[0]):
        return jsonify(success=True, message="Test version deleted successfuly")

    return jsonify(success=False, error=command_execution[1])


@TestSpecification_views.route("/save_step_data", methods=['POST'])
@role_required('editor', 'admin', 'editor')
@login_required
def save_step_data():
    data = request.get_json()
    step_id = data.get('id')
    actions_data = data.get('actions_data')
    results_data = data.get('results_data')

    result = TestSteps.update_step_info(step_id, actions_data, results_data)

    if (not result[0]):
        return jsonify(success=False, error=f"It was not possible to save the step {step_id} error: {result[1]}")

    return jsonify(success=True, message="Step saved")


@TestSpecification_views.route("/new_step", methods=['POST'])
@role_required('editor', 'admin', 'editor')
@login_required
def new_step():
    data = request.get_json()
    test_id = data.get('test_id')
    actions = data.get('actions_data')
    results = data.get('results_data')
    previous_step = data.get('previous_step_id')

    testcase = TestCases.return_testcase_by_id(test_id)

    if (not testcase):
        return jsonify(success=False, error="test case for this step was not found")

    results = TestSteps.create_new_step(
        actions,
        results,
        testcase["id"],
        testcase["current_version"],
        previous_step
    )

    if (results[0]):
        return jsonify(success=True, message="Step saved: "+results[1])

    return jsonify(success=False, error="Step not saved: "+results[1])


@TestSpecification_views.route("/delete_step", methods=['POST'])
@role_required('editor', 'admin', 'editor')
@login_required
def delete_step():
    data = request.get_json()
    step_id = data.get('step_id')
    test_id = data.get('test_id')

    test_version = TestCases.return_testcase_by_id(test_id)["current_version"]
    results = TestSteps.delete_step(step_id, test_id, test_version)

    if (results[0]):
        return jsonify(success=True, message=f"Step {step_id} deleted")

    return jsonify(success=False, error=f"Step {step_id} was not deleted. error: "+results[1])


@TestSpecification_views.route("/set_edit_mode", methods=['POST'])
@role_required('editor', 'admin', 'editor')
@login_required
def set_edit_mode():
    data = request.get_json()
    edit_mode = data.get('edit_mode')

    session["editing_steps"] = edit_mode
    return jsonify(success=True, message="edit mode updated")


@TestSpecification_views.route("/get_edit_mode", methods=['GET'])
def get_edit_mode():

    current_user.editing_steps

    return jsonify(success=True, data=current_user.editing_steps, message="edit mode updated")


@TestSpecification_views.route("/reorder_steps", methods=['POST'])
@role_required('editor', 'admin', 'editor')
@login_required
def reorder_steps():
    data = request.get_json()
    test_case_id = data.get('id')
    steps_ids_in_order = data.get('steps')

    result = TestSteps.reorder_steps_position(steps_ids_in_order)

    if (not result.executed):
        return jsonify(success=False, error=f"It was not possible to chnage the steps order of the test {test_case_id}. error: {result.error}")

    return jsonify(success=True, message=f"steps updated for the test {test_case_id}")


@TestSpecification_views.route("/copy_step", methods=['POST'])
@role_required('editor', 'admin', 'editor')
@login_required
def copy_step():
    data = request.get_json()

    copied_step_id = data.get('copied_step_id')
    test_id = data.get('test_id')
    clicked_step_id = data.get("clicked_step_id")

    Old_step = TestSteps.return_step_by_id(copied_step_id)
    if (not Old_step[1]):
        return jsonify(success=False, error=f"Error readingf the step id {copied_step_id}")

    testcase = TestCases.return_testcase_by_id(test_id)

    if (not testcase):
        return jsonify(success=False, error=f"test case for the step {clicked_step_id} was not found")

    result = TestSteps.create_new_step(
        Old_step[0]["step_action"],
        Old_step[0]["expected_value"],
        testcase["id"],
        testcase["current_version"],
        clicked_step_id
    )
    if (not result[0]):
        return jsonify(success=False, error=f"Error copying the step  {copied_step_id}. error{result[1]}")
    return jsonify(success=True, message=f"step created successfuly")


@TestSpecification_views.route("/compare_test_versions", methods=['POST'])
@login_required
def compare_test_versions():
    data = request.get_json()
    test_id = data.get("id")[2:]
    left_dropdown_version = data.get("left_compare")
    right_dropdown_version = data.get("right_compare")

    _testcase = TestCases.return_testcase_by_id(test_id)

    if (not _testcase):
        return jsonify(success=False, error=f"It was not possible to execute the compare of the test {test_id}")

    # if the versions are not explicitaly sent, the current version and the newest one will be sent
    if (not left_dropdown_version and not right_dropdown_version):
        left_dropdown_version = _testcase["current_version"]
        right_dropdown_version = _testcase["versions"][-1]

    _teststepsV1 = TestSteps.return_steps_from_test_cases(
        test_id,
        left_dropdown_version
    )

    if (not _teststepsV1[0]):
        return jsonify(success=False, error=f"It was not possible to find steps for the test {test_id}")

    _teststepsV2 = TestSteps.return_steps_from_test_cases(
        test_id,
        right_dropdown_version  # newest version
    )

    if (not _teststepsV2[0]):
        return jsonify(success=False, error=f"It was not possible to find steps for the test {test_id}")

    return render_template(
        'partials/compare_versions.jinja2',
        testcase=_testcase,
        left_dropdown_version=left_dropdown_version,
        right_dropdown_version=right_dropdown_version,
        test_steps_v1=_teststepsV1[1],
        test_steps_v2=_teststepsV2[1],
    )


@TestSpecification_views.route("/get_user_level", methods=['GET'])
@login_required
def get_user_level():
    return jsonify(success=True, user_level=current_user.user_level, message="current user level")
