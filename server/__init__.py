from base64 import b64decode

from flask import Flask

import config

def create_app():
    app = Flask(__name__)
    app.app_context().push()

    app.secret_key = b64decode(config.app_secret_key())

    return app


global_app = create_app()
