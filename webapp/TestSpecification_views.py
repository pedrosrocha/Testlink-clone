from flask import Blueprint, render_template, request,  session, abort, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from webapp.utils.roles_controllers import role_required
from webapp.Parameters.projects import projects
from webapp.Parameters.TestSuites import TestSuits
from webapp.Parameters.TestCases import TestCases
from webapp.Parameters.TestSteps import TestSteps
from webapp.Parameters.FileHandler import files


TestSpecification_views = Blueprint('TestSpecification_views', __name__)


@TestSpecification_views.route('/TestSpecification', methods=['GET', 'POST'])
@login_required
def TestSpecification():
    if request.method == 'GET':
        if (not session.get('current_project_id')):
            _current_project_id = int(
                projects.return_oldest_project().data["id"])
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
@login_required
def get_test_tree_root():

    _current_project_id = session.get('current_project_id')
    if (not _current_project_id):
        _current_project_id = int(
            projects.return_oldest_project().data["id"])

        session["current_project_id"] = int(_current_project_id)

    command = TestSuits.return_testsuits_from_project(
        _current_project_id,
        None
    )

    if not command.executed:
        return jsonify(success=False, message="Error while acquiring the root suite", error=command.error), 404

    return jsonify([
        {
            'id': suite["id"],
            'text': suite["name"],
            'type': "suite",
            'children': True  # Enables lazy loading
        } for suite in command.data
    ])


@TestSpecification_views.route('/get_test_tree_children')
@login_required
def get_test_tree_children():
    node_id = request.args.get('id')  # Node id returned from jstree

    _current_project_id = session.get('current_project_id')
    if (not _current_project_id):
        _current_project_id = int(
            projects.return_oldest_project().data["id"])
        session["current_project_id"] = int(_current_project_id)

    children = []

    if not node_id:
        return jsonify(success=False, message="No id provided", error=command.error), 404

    suite_id = int(node_id)

    command = TestSuits.return_testsuits_from_project(
        _current_project_id,
        suite_id
    )

    if not command.executed:
        return jsonify(success=False, message="Error while reading the suites", error=command.error), 404

    for suite in command.data:
        children.append({
            'id': suite["id"],
            'text': suite["name"],
            'type': "suite",
            'children': True  # This is what makes the jstrre lazy loading possible
        })

    command = TestCases.return_testcases_from_project(suite_id)

    if not command.executed:
        abort(404)

    for case in command.data:
        children.append({
            'id': f'c_{case["id"]}',
            'text': str(case["id"])+":"+case["name"],
            'type': "test",
            'children': False  # Leaf node
        })

    return jsonify(children)


@TestSpecification_views.route('/delete_node', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def delete_node():
    data = request.get_json()
    id = data.get('id')
    type = data.get('type')

    if (type == "suite"):
        command = TestSuits.delete_suite(id)
        if command.executed:
            return jsonify(success=True, message=command.message)

        return jsonify(success=False, error=command.error), 500

    # else: type == test
    id = id[2:]
    delete_command = TestCases.delete_test_case(id)
    if delete_command.executed:
        return jsonify(success=True, message=delete_command.message)

    return jsonify(success=False, error=delete_command.error), 500


@TestSpecification_views.route('/rename_node', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def rename_node():
    data = request.get_json()
    id = data.get('id')
    new_name = data.get('new_name')
    type = data.get('type')

    if (type == "suite"):
        command = TestSuits.update_suite_data(
            id,
            name=new_name
        )
        if command.executed:
            return jsonify(success=True, message=command.message), 200

        return jsonify(success=False, error=command.error), 500

    # else: type == test
    current_user_name = current_user.username
    id = id[2:]
    update_command = TestCases.update_testcase_data(
        id,
        name=new_name,
        last_updated_by=current_user_name
    )
    if update_command.executed:
        return jsonify(success=True, message=update_command.message)

    return jsonify(success=False, error=update_command.error), 500


@TestSpecification_views.route('/add_test_case', methods=['POST'])
@login_required
@role_required('admin', 'editor')
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
    command = TestCases.add_testcase(
        node_name,
        description,
        precondition,
        expected_results,
        status,
        priority,
        parent_id,
        current_user_name,
        current_user_name
    )
    if not command.executed:
        return jsonify(success=False, error=command.error, name=node_name, id=0), 500

    return jsonify(success=True, message=command.message, name=node_name, id=command.data), 200


@TestSpecification_views.route('/add_suite', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def add_suite():
    data = request.get_json()
    node_name = data.get('name')
    parent_id = data.get('parent_id')
    description = data.get('description') if data.get('description') else ""

    _current_project_id = session.get('current_project_id')
    if (not _current_project_id):
        _current_project_id = int(
            projects.return_oldest_project().data["id"])
        session["current_project_id"] = int(_current_project_id)

    current_user.username
    command = TestSuits.add_suite(
        node_name,
        description,
        parent_id,
        _current_project_id,
        current_user.username
    )

    if not command.executed:
        return jsonify(success=False, message=command.message, error=command.error, name=node_name, id=command.data), 400
    return jsonify(success=True,  message=command.message, name=node_name, id=command.data), 201


@TestSpecification_views.route('/paste_test_case', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def paste_test_case():
    data = request.get_json()
    test_case_id = data.get('test_id')
    parent_id = data.get('parent_id')

    # removes the "c_" from the string and transforms to integer
    test_case_id = int(test_case_id[2:])
    parent_id = int(parent_id)

    command = TestCases.copy_test_case(
        parent_id,
        test_case_id,
        current_user.username
    )
    if command.data:
        current_version_to_copy = TestCases.return_testcase_by_id(test_case_id).data[
            "current_version"
        ]

        copy_command = TestSteps.copy_steps(
            test_case_id,
            current_version_to_copy,
            command.data
        )
        if not copy_command.executed:
            return jsonify(success=False, error=copy_command.error), 500

        return jsonify(success=True, message=command.message + "\n"+copy_command.message), 201

    return jsonify(success=False, error=command.error), 500


@TestSpecification_views.route('/paste_suite', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def paste_suite():
    data = request.get_json()
    suite_id = data.get('suite_id')              # root suite being copied
    parent_id = data.get('parent_id')            # new parent node

    _current_project_id = session.get('current_project_id')
    if (not _current_project_id):
        _current_project_id = int(
            projects.return_oldest_project().data["id"])
        session["current_project_id"] = int(_current_project_id)

    # flat list of all child nodes (suites & tests)
    children = data.get("children")

    # Map old IDs to new ones
    id_map = {}

    # Create the root suite first
    copied_suite_command = TestSuits.copy_suite(
        parent_id,
        suite_id,
        current_user.username,
        _current_project_id
    )

    if not copied_suite_command.executed:
        return jsonify(success=False, error=copied_suite_command.error), 500

    id_map[suite_id] = copied_suite_command.data  # link old to new

    for child in children:
        old_parent_id = child["parent"]
        old_id = child["id"]

        new_parent_id = id_map.get(old_parent_id)
        if not new_parent_id:
            return jsonify(success=False, error=f"Missing parent mapping for {old_parent_id}"), 400

        if old_id.startswith('c_'):  # test case
            command = TestCases.copy_test_case(
                new_parent_id,
                old_id[2:],  # remove prefix 'c_'
                current_user.username
            )
            if not command.data:
                return jsonify(success=False, error=command.error), 500

            current_version_to_copy = TestCases.return_testcase_by_id(old_id[2:]).data[
                "current_version"
            ]
            TestSteps.copy_steps(
                old_id[2:],  # remove prefix 'c_')
                current_version_to_copy,
                command.data
            )

        else:  # suite
            command_suite = TestSuits.copy_suite(
                new_parent_id,
                old_id,
                current_user.username,
                _current_project_id
            )

            if not command_suite.executed:
                return jsonify(success=False, error=f"Could not create suite {old_id}"), 500

            id_map[old_id] = command_suite.data  # store mapping

    return jsonify(success=True, message="Project updated successfully"), 201


@TestSpecification_views.route('/move_suite', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def move_suite():
    data = request.get_json()
    suite_id = data.get('node_id')
    parent_id = data.get('parent_id')            # new parent node
    _current_project_id = session.get('current_project_id')
    if (not _current_project_id):
        _current_project_id = int(
            projects.return_oldest_project().data["id"])
        session["current_project_id"] = int(_current_project_id)

    command = TestSuits.update_suite_data(
        suite_id,
        None,
        _current_project_id,
        None,
        parent_id
    )

    if command.executed:
        return jsonify(success=True, message=command.message), 200

    return jsonify(success=False, error=command.error), 500


@TestSpecification_views.route('/move_test', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def move_test():
    data = request.get_json()

    test_id = data.get('node_id')
    test_id = test_id[2:]

    parent_id = data.get('parent_id')            # new parent node

    test_case_move = TestCases.update_testcase_data(
        test_id,
        None,
        parent_id,
        None,
        None,
        None,
        None,
        None,
        None
    )

    if test_case_move.executed:
        return jsonify(success=True, message="test case moved successfuly")

    return jsonify(success=False, error=test_case_move.error), 500


@TestSpecification_views.route('/get_testcase_html/<int:testcase_id>', methods=['GET'])
@login_required
def get_testcase_html(testcase_id):
    testcase_command = TestCases.return_testcase_by_id(testcase_id)
    if not testcase_command.executed:
        abort(404)

    teststeps = TestSteps.return_steps_from_test_cases(
        testcase_command.data["id"],
        testcase_command.data["current_version"]
    )

    if not teststeps.executed:
        abort(404)

    return render_template(
        'partials/testcase_card.jinja2',
        testcase=testcase_command.data,
        test_steps=teststeps.data,
        editing_steps=session.get('editing_steps'),
        user=current_user
    )


@TestSpecification_views.route('/get_suite_html/<int:suite_id>', methods=['GET'])
@login_required
def get_suite_html(suite_id):
    command = TestSuits.return_suite_by_id(suite_id)

    if not command.executed:
        abort(404)

    return render_template(
        'partials/testsuite_card.jinja2',
        suite=command.data,
        user=current_user
    )


@TestSpecification_views.route("/new_test_case_form", methods=['GET'])
@login_required
@role_required('admin', 'editor')
def new_test_case_form():
    return render_template('partials/add_new_test_case.html')


@TestSpecification_views.route("/edit_suite", methods=['POST'])
@login_required
@role_required('admin', 'editor')
def edit_suite():
    data = request.get_json()
    suite_id = data.get('id')

    command = TestSuits.return_suite_by_id(suite_id)
    if not command.executed:
        abort(404)
    return render_template('partials/edit_suite.jinja2', suite=command.data)


@TestSpecification_views.route("/edit_test_case", methods=['POST'])
@login_required
@role_required('admin', 'editor')
def edit_test_case():
    data = request.get_json()
    test_id = data.get('id')

    # removes the "c_" from the string and transforms to integer
    test_id = int(test_id[2:])

    current_test_case = TestCases.return_testcase_by_id(test_id)
    if not current_test_case.executed:
        abort(404)
    return render_template('partials/edit_test_case.jinja2', testcase=current_test_case.data)


@TestSpecification_views.route("/new_suite_form", methods=['GET'])
@login_required
@role_required('admin', 'editor')
def new_suite_form():
    return render_template('partials/add_new_suite.html')


@TestSpecification_views.route("/update_test_case", methods=['POST'])
@login_required
@role_required('admin', 'editor')
def update_test_case():
    data = request.get_json()
    id = data.get('id')[2:]
    name = data.get('name')
    description = data.get('description')
    preconditions = data.get('preconditions')
    expected_results = data.get('expected_results')
    priority = data.get('priority')
    status = data.get('status')

    testcase_update = TestCases.update_testcase_data(
        id,
        name,
        False,
        description,
        preconditions,
        expected_results,
        priority,
        status,
        current_user.username
    )
    if (testcase_update.executed):
        return jsonify(success=True, message=testcase_update.message)

    return jsonify(success=False, error=testcase_update.error), 500


@TestSpecification_views.route("/update_suite", methods=['POST'])
@login_required
@role_required('admin', 'editor')
def update_suite():
    data = request.get_json()
    id = data.get('id')
    name = data.get('name')
    description = data.get('description')

    command = TestSuits.update_suite_data(
        id,
        name,
        False,
        description,
        None
    )

    if (command.executed):
        return jsonify(success=True, message=command.message), 200

    return jsonify(success=False, error=command.error), 500


@TestSpecification_views.route("/new_test_case_version", methods=['POST'])
@login_required
@role_required('admin', 'editor')
def new_test_case_version():
    data = request.get_json()
    id = data.get('id')[2:]

    testcase_previous_version = TestCases.return_testcase_by_id(id).data[
        "current_version"]

    new_version = TestCases.new_test_version(id, current_user.username)
    if (new_version.executed):
        testcase_new_version = TestCases.return_testcase_by_id(id).data[
            "current_version"
        ]

        TestSteps.copy_steps_new_version(
            id,
            testcase_previous_version,
            testcase_new_version
        )

        return jsonify(success=True, message=new_version.message), 201

    return jsonify(success=False, error=new_version.error), 500


@TestSpecification_views.route("/update_test_case_version", methods=['POST'])
@login_required
@role_required('admin', 'editor')
def update_test_case_version():
    data = request.get_json()
    id = data.get('id')
    version = data.get("version")

    change_version = TestCases.update_testcase_data(
        id,
        current_version=version
    )
    if (change_version.executed):
        return jsonify(success=True, message="Test version created successfuly")

    return jsonify(success=False, error=change_version.error), 500


@TestSpecification_views.route("/delete_testcase_version", methods=['POST'])
@login_required
@role_required('admin', 'editor')
def delete_testcase_version():
    data = request.get_json()
    id = data.get('id')[2:]

    command_execution = TestCases.delete_current_version(id)
    if (command_execution.executed):
        return jsonify(success=True, message=command_execution.message)

    return jsonify(success=False, error=command_execution.error), 500


@TestSpecification_views.route("/save_step_data", methods=['POST'])
@login_required
@role_required('editor', 'admin')
def save_step_data():
    data = request.get_json()
    step_id = data.get('id')
    actions_data = data.get('actions_data')
    results_data = data.get('results_data')

    command_step = TestSteps.update_step_info(
        step_id,
        actions_data,
        results_data
    )

    if (not command_step.executed):
        return jsonify(success=False, error=command_step.error), 500

    return jsonify(success=True, message=command_step.message)


@TestSpecification_views.route("/new_step", methods=['POST'])
@login_required
@role_required('editor', 'admin')
def new_step():
    data = request.get_json()
    test_id = data.get('test_id')
    actions = data.get('actions_data')
    results = data.get('results_data')
    previous_step = data.get('previous_step_id')

    testcase = TestCases.return_testcase_by_id(test_id)

    if (not testcase.executed):
        return jsonify(success=False, error=testcase.error), 404

    results = TestSteps.create_new_step(
        actions,
        results,
        testcase.data["id"],
        testcase.data["current_version"],
        previous_step
    )

    if (results.executed):
        return jsonify(success=True, message="Step saved: "+results.message), 201

    return jsonify(success=False, error="Step not saved: "+results.error), 500


@TestSpecification_views.route("/delete_step", methods=['POST'])
@login_required
@role_required('editor', 'admin')
def delete_step():
    data = request.get_json()
    step_id = data.get('step_id')
    test_id = data.get('test_id')

    test_version = TestCases.return_testcase_by_id(
        test_id).data["current_version"]
    results = TestSteps.delete_step(step_id, test_id, test_version)

    if (results.executed):
        return jsonify(success=True, message=results.message)

    return jsonify(success=False, error=f"Step {step_id} was not deleted. error: "+results.error), 500


@TestSpecification_views.route("/set_edit_mode", methods=['POST'])
@login_required
@role_required('editor', 'admin')
def set_edit_mode():
    data = request.get_json()
    edit_mode = data.get('edit_mode')

    session["editing_steps"] = edit_mode
    return jsonify(success=True, message="edit mode updated")


@TestSpecification_views.route("/get_edit_mode", methods=['GET'])
@login_required
def get_edit_mode():

    current_user.editing_steps

    return jsonify(success=True, data=current_user.editing_steps, message="edit mode updated")


@TestSpecification_views.route("/reorder_steps", methods=['POST'])
@login_required
@role_required('editor', 'admin')
def reorder_steps():
    data = request.get_json()
    test_case_id = data.get('id')
    steps_ids_in_order = data.get('steps')

    result = TestSteps.reorder_steps_position(steps_ids_in_order)

    if (not result.executed):
        return jsonify(success=False, error=f"It was not possible to change the steps order of the test {test_case_id}. error: {result.error}"), 500

    return jsonify(success=True, message=f"steps updated for the test {test_case_id}")


@TestSpecification_views.route("/copy_step", methods=['POST'])
@login_required
@role_required('editor', 'admin')
def copy_step():
    data = request.get_json()

    copied_step_id = data.get('copied_step_id')
    test_id = data.get('test_id')
    clicked_step_id = data.get("clicked_step_id")

    Old_step_command = TestSteps.return_step_by_id(copied_step_id)
    if (not Old_step_command.executed):
        return jsonify(success=False, error=f"Error reading the step id {copied_step_id}.\n"+Old_step_command.error), 404

    testcase = TestCases.return_testcase_by_id(test_id)

    if (not testcase.executed):
        return jsonify(success=False, error=f"test case for the step {clicked_step_id} was not found. \n"+testcase.error), 404

    result = TestSteps.create_new_step(
        Old_step_command.data["step_action"],
        Old_step_command.data["expected_value"],
        testcase.data["id"],
        testcase.data["current_version"],
        clicked_step_id
    )
    if (not result.executed):
        return jsonify(success=False, error=f"Error copying the step  {copied_step_id}. error{result.error}"), 500
    return jsonify(success=True, message=result.message), 201


@TestSpecification_views.route("/compare_test_versions", methods=['POST'])
@login_required
@role_required('editor', 'admin')
def compare_test_versions():
    data = request.get_json()
    test_id = data.get("id")[2:]
    left_dropdown_version = data.get("left_compare")
    right_dropdown_version = data.get("right_compare")

    _testcase = TestCases.return_testcase_by_id(test_id)

    if (not _testcase.executed):
        return jsonify(success=False, error=f"It was not possible to execute the compare of the test {test_id}. \n"+_testcase.error), 404

    # if the versions are not explicitaly sent, the current version and the newest one will be sent
    if (not left_dropdown_version and not right_dropdown_version):
        left_dropdown_version = _testcase.data["current_version"]
        right_dropdown_version = _testcase.data["versions"][-1]

    _teststepsV1 = TestSteps.return_steps_from_test_cases(
        test_id,
        left_dropdown_version
    )

    if (not _teststepsV1.executed):
        return jsonify(success=False, error=_teststepsV1.error), 404

    _teststepsV2 = TestSteps.return_steps_from_test_cases(
        test_id,
        right_dropdown_version  # newest version
    )

    if (not _teststepsV2.executed):
        return jsonify(success=False, error=_teststepsV2.error), 404

    return render_template(
        'partials/compare_versions.jinja2',
        testcase=_testcase.data,
        left_dropdown_version=left_dropdown_version,
        right_dropdown_version=right_dropdown_version,
        test_steps_v1=_teststepsV1.data,
        test_steps_v2=_teststepsV2.data,
    )


@TestSpecification_views.route("/get_user_level", methods=['GET'])
@login_required
def get_user_level():
    return jsonify(success=True, user_level=current_user.user_level, message="current user level")


@TestSpecification_views.route("/get_step", methods=['GET'])
@login_required
def get_step():
    step_id = request.args.get('step', type=int)

    if step_id is None:
        return jsonify(success=False, error=f"It wasd not posisble to get the step because no id was sent.")

    command = TestSteps.return_step_by_id(step_id)
    if not command.executed:
        return jsonify(success=False, error=f"It wasd not posisble to get the step {id} due to the error: {command.error}")

    return jsonify(success=True, step=command.data)


@TestSpecification_views.route('/upload_image', methods=['POST'])
@login_required
@role_required('editor', 'admin')
def upload_image():
    if 'file' not in request.files:
        return jsonify(success=False, error='No file part in the request'), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify(success=False, error='No selected file'), 400

    command = files.savefile(file, current_app.root_path)

    if command.executed:
        file_url = f'/static/uploads/{file.filename}'
        return jsonify({'location': file_url})

    return jsonify(success=False, error=command.error), 500
