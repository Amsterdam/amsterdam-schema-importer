from werkzeug.serving import run_simple
from dynapi.app import AppReloader
# from .app import app_factory as create_app

application = AppReloader()


if __name__ == '__main__':
    run_simple('localhost', 5001, application,
               use_reloader=True, use_debugger=True, use_evalex=True)
