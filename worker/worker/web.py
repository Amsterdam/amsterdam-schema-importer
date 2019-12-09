import os
from flask import Flask, request
from sqlalchemy import create_engine

from schema_ingest import (
    fetch_schema,
    create_table,
    create_rows,
)

from . import app as executors

app = Flask(__name__)

DB_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5435/postgres"
)

# Change this to use aproach as in dynapi
engine = create_engine(DB_URI)

@app.route('/mapfiles', methods=['POST'])
def create_mapfile():
    json_str = request.json
    return executors.CreateMapfileFromDataset()(json_str)


@app.route('/datasets', methods=['POST'])
def create_dataset():
    schema = fetch_schema(request.json)
    with engine.begin() as connection:
        create_table(schema, connection)
