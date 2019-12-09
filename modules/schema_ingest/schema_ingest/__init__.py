import os
import json
from sqlalchemy import MetaData
from sqlalchemy.schema import CreateTable
import jsonschema
from dataservices.amsterdam_schema import DatasetSchema
from schema_db import DBTable


# DB_URI = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@database/postgres")
DB_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5435/postgres"
)


metadata = MetaData()


def schema_def_from_path(schema_path):
    with open(schema_path) as fh:
        return json.load(fh)


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
