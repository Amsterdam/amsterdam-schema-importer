# Utils for using db in schema + data creation
from dataclasses import dataclass
import functools
from sqlalchemy import Table, Column, create_engine, MetaData, sql
from sqlalchemy import (
    String, Integer
)

from dataservices.amsterdam_schema import DatasetTableSchema


JSON_TYPE_TO_PG = {
    "string": String,
    "integer": Integer,
}

@dataclass
class DBTable:
    name: str
    schema: str
    columns: typing.List[Column]

    @classmethod
    def from_dataset_table(cls,
                           dataset_id: str, dataset_table: DatasetTableSchema):
        columns = [
            Column(
                field.name,
                JSON_TYPE_TO_PG[field.type]
            ) for field in dataset_table.fields
        ]
        return cls(
            name=dataset_table.id,
            schema=dataset_id,
            columns=columns
        )

    @property
    def pg_table(self) -> Table:
        return Table(
            self.name, MetaData(),
            schema=self.schema,
            *self.columns
        )


@functools.lru_cache(12)
def get_engine_from_db_uri(db_uri: str):
    """ SQLA engines should be defined once per process """
    return create_engine(db_uri)

class Postgres:
    # XXX Change to inject engine here.
    def __init__(self, db_uri: str):
        self.engine = get_engine_from_db_uri(
                db_uri
        )
        self.meta = MetaData(
            self.engine
        )
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

    def create_schema(self, schema_name: str):
        self.connection.execute(sql.text(
            "create schema :schema"
        ), schema=schema_name)

    def create_table(self, table: DBTable):
        table.pg_table.create(self.connection)

    def insert_row(self, table: DBTable, values):
        table.pg_table.insert(
            values
        )

    def commit(self):
        self.transaction.commit()
