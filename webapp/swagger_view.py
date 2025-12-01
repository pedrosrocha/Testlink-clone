from flask import Blueprint, render_template, request,  session, abort, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from webapp.utils.roles_controllers import role_required
from webapp.Parameters.projects import projects
from webapp.Parameters.TestSuites import TestSuits
from webapp.Parameters.TestCases import TestCases
from webapp.Parameters.TestSteps import TestSteps
from webapp.Parameters.FileHandler import files

swagger_view = Blueprint('swagger_view', __name__)


@swagger_view.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)
