from app import application
from werkzeug.middleware.proxy_fix import ProxyFix
import google.cloud.logging

application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1)

client = google.cloud.logging.Client()
client.setup_logging()

if __name__ == "__main__":
    application.run()
