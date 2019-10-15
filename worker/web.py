from flask import Flask, request
app = Flask(__name__)

from .app import main


@app.route('/mapfiles', methods=['POST'])
def create_mapfile():
    json_str = request.json
    return main(json_str)