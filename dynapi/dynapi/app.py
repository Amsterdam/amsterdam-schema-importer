from os import environ
from flask import Flask
from flask_api import FlaskAPI
from flask_sacore import SACore

dsn = environ["DATABASE_URL"]


class DynAPI(Flask):
    def __init__(self, import_name, **kwargs):
        super().__init__(import_name, **kwargs)
        self.db = self.fetch_db(self)

    def fetch_db(self, app):
        return SACore(dsn, app)


def app_factory():

    # import and register blueprints
    from .api import api  # NoQA

    app = DynAPI(__name__)
    app.register_blueprint(api)
    app.config["DEFAULT_RENDERERS"] = [
        "flask_api.renderers.JSONRenderer",
        "flask_api.renderers.BrowsableAPIRenderer",
    ]
    return app