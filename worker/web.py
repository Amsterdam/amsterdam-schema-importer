from flask import Flask, request
app = Flask(__name__)

from . import app as executors


@app.route('/mapfiles', methods=['POST'])
def create_mapfile():
    json_str = request.json
    return executors.CreateMapfileFromDataset()(json_str)