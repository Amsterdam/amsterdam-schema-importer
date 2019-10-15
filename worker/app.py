from flask import Flask
app = Flask(__name__)


@app.route('/mapfiles', methods=['POST'])
def create_mapfile():
    return 'Hello, World!'