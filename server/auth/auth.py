import secrets
import string

import flask
from flask_login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
    UserMixin
)

import requests

import google_auth_oauthlib.flow
from google.auth.transport import requests as google_auth_requests
from google.oauth2 import id_token

from server import global_app as app
from server.datastore_models import users
import config

GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'

CLIENT_SECRETS_FILE = config.google_client_secret_filename()
SCOPES = ['openid',
          'https://www.googleapis.com/auth/userinfo.profile',
          'https://www.googleapis.com/auth/userinfo.email']

auth_blueprint = flask.Blueprint('auth', __name__)

login_manager = LoginManager()
login_manager.init_app(app)


class UserForAuth(UserMixin):
    def __init__(self, user):
        self.id = user.key.name
        self.email = user.get(users.User.email)
        self.perms = user.get(users.User.perms)

    @staticmethod
    def get(user_id):
        user = users.User.get(user_id)
        if not user:
            return None

        user = UserForAuth(user)
        return user

    @staticmethod
    def create(user_id, email):
        user = users.User.create(user_id, email)
        return UserForAuth(user)


@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


@login_manager.user_loader
def load_user(user_id):
    return UserForAuth.get(user_id)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def random_string(length=10):
    password_characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(password_characters) for i in range(length))


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


@auth_blueprint.route("/login")
def login():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)
    # https://github.com/googleapis/google-auth-library-python-oauthlib/issues/46
    # need 43-128 char
    # need to manually set because of bug in library
    flow.code_verifier = random_string(128)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for('auth.oauth2callback', _external=True, _scheme='https')

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state
    flask.session['code_verifier'] = flow.code_verifier

    return flask.redirect(authorization_url)


@auth_blueprint.route('/login/callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('auth.oauth2callback', _external=True, _scheme='https')
    # need to manually set because of bug in library
    flow.code_verifier = flask.session['code_verifier']

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    request = google_auth_requests.Request()

    id_info = id_token.verify_oauth2_token(
        credentials.id_token, request, flow.client_config['client_id'])

    if id_info['iss'] != 'https://accounts.google.com':
        return flask.redirect(flask.url_for('home.main'))

    user_id = id_info.get('sub')
    email = id_info.get('email')
    if not user_id or not email:
        flask.flash('Did not get user id and/or email from Google')
        return flask.redirect(flask.url_for('home.main'))

    allowed_email_domain = config.allowed_email_domain()
    is_allowed_email = email.endswith(allowed_email_domain)
    if not is_allowed_email:
        return flask.redirect(flask.url_for('home.main'))

    user = UserForAuth.get(user_id)
    if not UserForAuth.get(user_id):
        user = UserForAuth.create(user_id, email)

    login_user(user)

    return flask.redirect(flask.url_for('home.main'))


@auth_blueprint.route("/logout")
@login_required
def logout():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    logout_user()
    return flask.redirect(flask.url_for("home.main"))

