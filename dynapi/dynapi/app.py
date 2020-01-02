import os
from flask import Flask
from flask_cors import CORS
from flask_sacore import SACore
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


dsn = os.getenv("DATABASE_URL")

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN is not None:
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[FlaskIntegration()])


class DynAPI(Flask):
    def __init__(self, import_name, **kwargs):
        super().__init__(import_name, **kwargs)
        self.db = self.fetch_db(self)

    def fetch_db(self, app):
        return SACore(dsn, app)


def create_app():
    from .api import api  # NoQA
    from .status import status  # NoQA
    app = DynAPI(__name__)
    CORS(app)

    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(status, url_prefix="/status")
    return app
