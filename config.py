from base64 import b64decode
import configparser


CONFIG_FILENAME = 'config.ini'

config = configparser.ConfigParser()
config.read(CONFIG_FILENAME)


def app_secret_key():
    return config['App']['SECRET_KEY']


def bootstrap_admin():
    return config['App']['BOOTSTRAP_ADMIN']


def allowed_email_domain():
    return config['App']['ALLOWED_EMAIL_DOMAIN']


def hackerrank_api_key():
    return config['Hackerrank']['API_KEY']


def google_client_secret_filename():
    return config['Google']['CLIENT_SECRET_FILENAME']
