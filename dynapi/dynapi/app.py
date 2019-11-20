from os import environ
from flask import Flask
from flask_cors import CORS
from flask_sacore import SACore


dsn = environ["DATABASE_URL"]


class DynAPI(Flask):
    def __init__(self, import_name, **kwargs):
        super().__init__(import_name, **kwargs)
        self.db = self.fetch_db(self)

    def fetch_db(self, app):
        return SACore(dsn, app)


def create_app():
    from .api import api  # NoQA
    app = DynAPI(__name__)
    CORS(app)
    app.register_blueprint(api)
    return app
