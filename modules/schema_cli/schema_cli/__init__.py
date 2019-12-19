import os
import click
from sqlalchemy import create_engine

from schema_ingest import (
    create_table,
    set_grants,
    create_rows,
    fetch_table_create_stmts,
    fetch_row_insert_stmts,
    schema_def_from_path,
    fetch_schema,
    fetch_rows,
)

DB_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5434/postgres"
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
            set_grants(schema, connection)
    else:
        print(fetch_table_create_stmts(schema))


@ingest.command()
@click.argument("dataset_table_name")
@click.argument("schema_path")
@click.argument("ndjson_path")
@click.option("--dry-run", is_flag=True, default=False)
def records(dataset_table_name, schema_path, ndjson_path, dry_run):
    # Add batching for rows.
    schema = fetch_schema(schema_def_from_path(schema_path))
    srid = schema["crs"].split(":")[-1]
    dataset_table = schema.get_table_by_id(dataset_table_name)
    with open(ndjson_path) as fh:
        data = list(fetch_rows(fh, srid))
    if not dry_run:
        engine = create_engine(DB_URI)
        with engine.begin() as connection:
            create_rows(schema, dataset_table, data, connection)
    else:
        print(fetch_row_insert_stmts(schema, dataset_table, data))
