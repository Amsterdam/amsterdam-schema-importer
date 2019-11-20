from dataclasses import dataclass
import typing

from sqlalchemy import Table, Column, create_engine, MetaData
from sqlalchemy import (
    String,
)

from dataservices.amsterdam_schema import Dataclass


JSON_TYPE_TO_PG = {
    "string": String
}

@dataclass
class DatasetTable:
    name: str
    schema: str
    columns: typing.List[Column]

    @classmethod
    def from_dataclass(cls, dataset_id: str, dclass: Dataclass):
        columns = [
            Column(
                field.name,
                JSON_TYPE_TO_PG[field.type]
            ) for field in dclass.fields
        ]
        return cls(
            name=dclass.name,
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


class PostgresPort:
    def __init__(self, db_uri: str):
        self.engine = create_engine(
                db_uri
        )
        self.meta = MetaData(
            self.engine
        )
        self.connection = self.engine.connect()
        self.transaction = self.engine.begin()
    
    def create_table(self, table: DatasetTable):
        table.pg_table.create(self.transaction)

    def insert_row(self, table: DatasetTable, **values):
        table.pg_table.insert(
            **values
        )

    def commit(self):
        self.transaction.commit()
