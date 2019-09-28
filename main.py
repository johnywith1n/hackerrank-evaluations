from app import application
from werkzeug.middleware.proxy_fix import ProxyFix

application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1)

if __name__ == "__main__":
    application.run()
