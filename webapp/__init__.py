from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from webapp.Parameters.users import testclone_user_list
from webapp.config import Config


def create_app():
    from webapp.Parameters.users import testclone_user

    app = Flask(__name__)

    app.config.from_object(Config)

    from .auth_views import auth
    from .projects_views import projects_views
    from .users_views import users_views
    from .TestSpecification_views import TestSpecification_views

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(projects_views, url_prefix='/')
    app.register_blueprint(users_views, url_prefix='/')
    app.register_blueprint(TestSpecification_views, url_prefix='/')

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    app.Users_manipulation = testclone_user_list(Bcrypt(app))

    @login_manager.user_loader
    def load_user(user_id):
        user = app.Users_manipulation.get_by_id(user_id)
        if user.executed:
            return testclone_user.from_dict(user.data)

        return None

    return app
