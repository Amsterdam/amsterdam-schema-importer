import os
import click
from sqlalchemy import create_engine
import ndjson
from shapely.geometry import shape

from schema_ingest import (
    create_table,
    create_rows,
    fetch_table_create_stmts,
    fetch_row_insert_stmts,
    schema_def_from_path,
    fetch_schema,
)

DB_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5435/postgres"
)


@click.group()
def main():
    pass


@main.group()
def ingest():
    pass


@ingest.command()
@click.argument("schema_path")
@click.option("--dry-run", default=False)
def table(schema_path, dry_run):
    schema = fetch_schema(schema_def_from_path(schema_path))
    if not dry_run:
        engine = create_engine(DB_URI)
        with engine.begin() as connection:
            create_table(schema, connection)
    else:
        print(fetch_table_create_stmts(schema))

def fetch_rows(ndjson_path):
    with open(ndjson_path) as fh:
        data = ndjson.load(fh)
        for row in data:
            row["geometry"] = shape(row["geometry"]).wkt
            yield row


@ingest.command()
@click.argument("dataset_table_name")
@click.argument("schema_path")
@click.argument("ndjson_path")
@click.option("--dry-run", is_flag=True, default=False)
def records(dataset_table_name, schema_path, ndjson_path, dry_run):
    # Add batching for rows.
    schema = fetch_schema(schema_def_from_path(schema_path))
    dataset_table = schema.get_table_by_id(dataset_table_name)
    data = list(fetch_rows(ndjson_path))
    if not dry_run:
        engine = create_engine(DB_URI)
        with engine.begin() as connection:
            create_rows(schema, dataset_table, data, connection)
    else:
        print(fetch_row_insert_stmts(schema, dataset_table, data))
