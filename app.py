from flask_login import (
    current_user,
)

# import this first to initialize our app
from server import global_app as application

from server.datastore_models.users import UserPermissions

from server.auth.auth import auth_blueprint
from server.views.home import home_blueprint
from server.views.admin import admin_blueprint
from server.views.assignment import assignment_blueprint
from server.views.overview import overview_blueprint

application.register_blueprint(home_blueprint)
application.register_blueprint(auth_blueprint)
application.register_blueprint(admin_blueprint)
application.register_blueprint(assignment_blueprint)
application.register_blueprint(overview_blueprint)

@application.context_processor
def inject_template_parameters():
    return dict(UserPermissions=UserPermissions,
                perms=current_user.perms)


if __name__ == "__main__":
    application.run(host='0.0.0.0', port=3100, ssl_context=('cert.pem', 'key.pem'))
