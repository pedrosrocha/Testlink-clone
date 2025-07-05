from flask import Blueprint, render_template, request, url_for, redirect, flash,  session, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from webapp.Parameters.users import testclone_user_list, testclone_user
from webapp.utils import url_parser
from webapp.utils.roles_controllers import role_required
from webapp.Parameters.projects import projects

TestSpecification_views = Blueprint('TestSpecification_views', __name__)


@TestSpecification_views.route('/TestSpecification', methods=['GET', 'POST'])
@login_required
def TestSpecification():
    if request.method == 'GET':
        _current_project_id = session.get('current_project_id')
        return render_template('test_specification.jinja2',
                               projects=projects.return_all_projects(),
                               current_project_id=int(_current_project_id),
                               user=current_user)


@TestSpecification_views.route('/Get_tree_data', methods=['GET'])
@login_required
def test():
    pass

    # return all testcases
    # return all testsuites
