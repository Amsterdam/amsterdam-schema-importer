import os
import io
import http.client
from flask import Flask, request
from sqlalchemy import create_engine
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from schema_ingest import (
    schema_def_from_url,
    fetch_schema,
    create_table,
    create_rows,
    fetch_rows,
)


from . import app as executors


SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN is not None:
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[FlaskIntegration()])

# sentry_sdk.init(dsn=SENTRY_DSN)
app = Flask(__name__)
# app = SentryWsgiMiddleware(app)

DB_DSN = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/postgres"
)

SCHEMA_URL = os.getenv("SCHEMA_URL")

# Change this to use aproach as in dynapi
engine = create_engine(DB_DSN)


@app.route("/mapfiles", methods=["POST"])
def create_mapfile():
    json_str = request.json
    return executors.CreateMapfileFromDataset()(json_str)


@app.route("/datasets", methods=["POST"])
def create_dataset():
    schema = fetch_schema(request.json)
    with engine.begin() as connection:
        create_table(schema, connection)
    return "", http.client.NO_CONTENT


@app.route("/<dataset>/<table>/rows", methods=["POST"])
def add_rows(dataset, table):
    schema_def = schema_def_from_url(SCHEMA_URL, dataset, table)
    schema = fetch_schema(schema_def)
    srid = schema["crs"].split(":")[-1]
    dataset_table = schema.get_table_by_id(table)
    # Naive non-streaming for now
    buf = io.StringIO(request.data.decode("utf-8"))
    data = list(fetch_rows(buf, srid))
    with engine.begin() as connection:
        create_rows(schema, dataset_table, data, connection)
    return "", http.client.NO_CONTENT


@app.route("/err")
def trigger_error():
    raise Exception("test error endpoint")
