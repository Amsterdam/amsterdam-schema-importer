import os
import json
import requests
from sqlalchemy import MetaData
from sqlalchemy.schema import CreateTable
import jsonschema
import ndjson
from shapely.geometry import shape
from dataservices.amsterdam_schema import DatasetSchema
from schema_db import DBTable


# DB_URI = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@database/postgres")
DB_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5435/postgres"
)


# XXX This is the regular approach, a 'global' metadata
# But somewhat problematic with the re-creation of DBTable on every request
metadata = MetaData()


def schema_def_from_path(schema_path):
    with open(schema_path) as fh:
        return json.load(fh)


def fetch_rows(fh):
    data = ndjson.load(fh)
    for row in data:
        row["geometry"] = shape(row["geometry"]).wkt
        yield row


def schema_def_from_url(schemas_url, dataset_name, table_name):
    response = requests.get(schemas_url)
    response.raise_for_status()
    for schema_dir_info in response.json():
        cur_ds_name = schema_dir_info["name"]
        if dataset_name == cur_ds_name:
            response = requests.get(f"{schemas_url}{cur_ds_name}/")
            response.raise_for_status()
            for schema_file_info in response.json():
                cur_table_name = schema_file_info["name"]
                if table_name == cur_table_name:
                    response = requests.get(f"{schemas_url}{cur_ds_name}/{cur_table_name}")
                    response.raise_for_status()
                    return response.json()
            break


def fetch_schema(schema_def):
    return DatasetSchema(schema_def)


def fetch_table_create_stmts(schema):
    for dataset_table in schema.tables:
        db_table = DBTable.from_dataset_table(metadata, schema.id, dataset_table)
    return str(CreateTable(db_table.pg_table))


def fetch_row_insert_stmts(schema, dataset_table, data):
    db_table = DBTable.from_dataset_table(metadata, schema.id, dataset_table)
    # XXX
    return str(db_table.pg_table.insert().compile())


def create_table(schema, connection):
    dataset_name = schema["id"]
    connection.execute(
        f"DROP SCHEMA IF EXISTS {dataset_name} CASCADE; CREATE SCHEMA {dataset_name}"
    )
    connection.execute(fetch_table_create_stmts(schema))


def create_rows(schema, dataset_table, data, connection):
    db_table = DBTable.from_dataset_table(metadata, schema.id, dataset_table)
    # XXX Validation crashes on null values
    # Extend to ["string", nulll] types
    if False:
        for row in data:
            try:
                dataset_table.validate(row)
            except jsonschema.exceptions.ValidationError as e:
                print(f"error: {e.message} for {row}")
    connection.execute(db_table.pg_table.insert().values(), data)
