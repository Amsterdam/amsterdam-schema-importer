# Utils for using db in schema + data creation
import typing
from dataclasses import dataclass
import functools
from sqlalchemy import Table, Column, create_engine, MetaData, sql
from sqlalchemy import String, Integer, Float, Boolean
from geoalchemy2 import Geometry
from sqlalchemy.schema import CreateTable


from dataservices.amsterdam_schema import DatasetSchema, DatasetTableSchema

# XXX make the srid configurable, is contained in aschema

JSON_TYPE_TO_PG = {
    "string": String,
    "boolean": Boolean,
    "integer": Integer,
    "number": Float,
    "https://schemas.data.amsterdam.nl/schema@v1.1.0#/definitions/id": String,
    "https://schemas.data.amsterdam.nl/schema@v1.1.0#/definitions/class": String,
    "https://schemas.data.amsterdam.nl/schema@v1.1.0#/definitions/dataset": String,
    "https://schemas.data.amsterdam.nl/schema@v1.1.0#/definitions/schema": String,
    "https://geojson.org/schema/Geometry.json": Geometry(geometry_type="GEOMETRY", srid=28992),
    "https://geojson.org/schema/Point.json": Geometry(geometry_type="POINT", srid=28992),
}


@dataclass
class DBTable:
    metadata: MetaData
    name: str
    dataset: DatasetSchema
    columns: typing.List[Column]

    @classmethod
    def from_dataset_table(
        cls, metadata, dataset: DatasetSchema, dataset_table: DatasetTableSchema
    ):
        columns = [
            Column(field.name, JSON_TYPE_TO_PG[field.type])
            for field in dataset_table.fields
        ]
        return cls(
            metadata=metadata, name=dataset_table.id, dataset=dataset, columns=columns
        )

    @property
    def pg_table(self) -> Table:
        # XXX maybe always pre-create the pg table on init
        table_key = f"{self.dataset.id}.{self.name}"
        table = self.metadata.tables.get(table_key)
        return (
            table
            if table is not None
            else Table(self.name, self.metadata, schema=self.dataset.id, *self.columns)
        )


@functools.lru_cache(12)
def get_engine_from_db_uri(db_uri: str):
    """ SQLA engines should be defined once per process """
    return create_engine(db_uri)


class Postgres:
    # XXX Change to inject engine here.
    def __init__(self, engine):
        self.engine = None
        return
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

    def create_schema(self, schema_name: str):
        self.connection.execute(sql.text("create schema :schema"), schema=schema_name)

    def create_table(self, table: DBTable):
        table.pg_table.create(self.connection)

    def fetch_table_dll(self, table: DBTable):
        return str(CreateTable(table.pg_table))

    def insert_row(self, table: DBTable, values):
        table.pg_table.insert(values)

    def commit(self):
        self.transaction.commit()
