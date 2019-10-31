from os import environ
from flask import Flask
from flask_cors import CORS
from flask_sacore import SACore


dsn = environ["DATABASE_URL"]
routes_root_dir = environ["ROUTES_ROOT_DIR"]


class DynAPI(Flask):
    def __init__(self, import_name, **kwargs):
        super().__init__(import_name, **kwargs)
        self.db = self.fetch_db(self)

    def fetch_db(self, app):
        return SACore(dsn, app)


def app_factory():

    # import and register blueprints
    from .api import api, make_routes  # NoQA

    app = DynAPI(__name__)
    CORS(app)
    app.register_blueprint(api)
    make_routes(app, routes_root_dir)
    return app


class AppReloader(object):
    _needs_reload = True

    def __init__(self):
        self.app = None # app_factory()

    @classmethod
    def reload(cls):
        print('reloading ..')
        cls._needs_reload = True

    def get_application(self):
        print('getting application ..')
        if self._needs_reload:
            print('recreating ..')
            self.app = app_factory()
            self.__class__._needs_reload = False

        return self.app

    def __call__(self, environ, start_response):
        app = self.get_application()
        print('__call__', app)
        return app(environ, start_response)
