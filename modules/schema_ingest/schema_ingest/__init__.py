import os
import json
import click
from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable
from dataservices.amsterdam_schema import DatasetSchema
from schema_db import Postgres, DBTable


# DB_URI = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@database/postgres")
DB_URI = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@localhost:5435/postgres")


metadata = MetaData()


def schema_from_path(path):
    with open(path) as fh:
        return json.load(fh)


def load_schema(schema):
    return DatasetSchema(schema)

def fetch_table_create_stmts(schema):
    pass

def create_table(schema):
    fetch_table_create_stmts(schema)


@click.command()
@click.argument("schema_path")
def main(schema_path):
    # path = "/home/jan/projects/amsterdam/amsterdam-schema-importer/data/bommen/bommen.dataset.schema.json"
    # engine = create_engine(DB_URI)
    schema = load_schema(schema_from_path(schema_path))
    # Create DDL
    # Need a Meta and an engine, maybe abstract ayway
    # db = Postgres(engine)
    for dataset_table in schema.tables:
        db_table = DBTable.from_dataset_table(
            metadata, schema.id, dataset_table
        )
    # print(db.fetch_table_dll(db_table))
    table = db_table.pg_table
    print(CreateTable(table))
    print(table.insert())
