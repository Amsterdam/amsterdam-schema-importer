import os
import json
import requests
from sqlalchemy import MetaData
from sqlalchemy.schema import CreateTable
import jsonschema
import ndjson
# from geoalchemy2.shape import from_shape
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


def fetch_rows(fh, srid):
    data = ndjson.load(fh)
    for row in data:
        row["geometry"] = f"SRID={srid};{shape(row['geometry']).wkt}"
        yield row


def schema_defs_from_url(schemas_url):
    schema_lookup = {}
    response = requests.get(schemas_url)
    response.raise_for_status()
    for schema_dir_info in response.json():
        schema_dir_name = schema_dir_info["name"]
        response = requests.get(f"{schemas_url}{schema_dir_name}/")
        response.raise_for_status()
        for schema_file_info in response.json():
            schema_name = schema_file_info["name"]
            response = requests.get(f"{schemas_url}{schema_dir_name}/{schema_name}")
            response.raise_for_status()
            schema_lookup[schema_name] = response.json()
    return schema_lookup


def schema_def_from_url(schemas_url, schema_name):
    return schema_defs_from_url(schemas_url)[schema_name]


def fetch_schema(schema_def):
    return DatasetSchema(schema_def)


def fetch_table_create_stmts(schema):
    create_stmts = []
    for dataset_table in schema.tables:
        db_table = DBTable.from_dataset_table(metadata, schema, dataset_table)
        create_stmts.append(str(CreateTable(db_table.pg_table)))
    return ";\n".join(create_stmts)


def fetch_row_insert_stmts(schema, dataset_table, data):
    db_table = DBTable.from_dataset_table(metadata, schema, dataset_table)
    # XXX
    return str(db_table.pg_table.insert().compile())


def create_table(schema, connection):
    dataset_name = schema["id"]
    connection.execute(
        f"DROP SCHEMA IF EXISTS {dataset_name} CASCADE; CREATE SCHEMA {dataset_name}"
    )
    connection.execute(fetch_table_create_stmts(schema))


# XXX could be made more fine-grained, GRANTS at col level SELECT(colname)
# TO <identity-mentioned-in-amsterdam-schema>, see Bert util.js grantStatements()

def set_grants(schema, connection):
    connection.execute(f"GRANT USAGE ON SCHEMA {schema.id} TO PUBLIC")
    for table in schema.tables:
        connection.execute(f"GRANT SELECT ON {schema.id}.{table.id} TO PUBLIC")


def create_rows(schema, dataset_table, data, connection):
    db_table = DBTable.from_dataset_table(metadata, schema, dataset_table)
    # XXX Validation crashes on null values
    # Extend to ["string", null] types
    if False:
        for row in data:
            try:
                dataset_table.validate(row)
            except jsonschema.exceptions.ValidationError as e:
                print(f"error: {e.message} for {row}")
    connection.execute(db_table.pg_table.insert().values(), data)
