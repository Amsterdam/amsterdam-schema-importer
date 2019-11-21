import json
import os

from dataclasses import dataclass
from dataservices.amsterdam_schema import DatasetSchema

from .core import types
from .ports import postgres

DATASETS_PATH = os.getenv("DATASET_PATH", "./data")
DB_URI = os.getenv(
    'DATABASE_URI', "postgresql://postgres:postgres@database/postgres"
)

def compose_dataset_path(schema_id: str, mkdirs: bool = True):
    dir_path = os.path.join(
        DATASETS_PATH, schema_id
    )
    filename = f"{schema_id}.schema.json" 
    if mkdirs:
        os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, filename)


@dataclass
class CreateDataset(types.Event):
    schema: dict


@dataclass
class DatasetCreated(types.Event):
    id: str


@dataclass
class CreateRow(types.Event):
    """ Create a document row """
    dataset_id: str
    dataset_table_id: str
    row: dict


@dataclass
class RowCreated(types.Event):
    """ Fact of an inserted row """
    dataset_id: str
    dataset_table_id: str
    row: dict


class DatasetService:
    """ Service to manage dataset entities.
        
        Existing entities:
         - **DatasetSchema**: jsonschema of a dataset
         - **Dataset**: domain of related data tables. Much like a schema in postgres.
         - **DatasetTable**: collection of data. Much like a table in postgresql.
         - **DatasetRow**: single row

         see https://github.com/Amsterdam/amsterdam-schema#concepts
    """
    registry: dict

    def __init__(self):
        handler_names = filter(
            lambda s: s.startswith("handle_"), dir(self)
        )
        handlers = dict(
            map(lambda n: (n, getattr(self, n)), handler_names)
        )
        self.registry = dict(
            [
                (f.__annotations__['event'], f) for
                name, f in handlers.items()
            ]
        )
    
    def _store_schema(self, schema: DatasetSchema):
        """ Store schema in schema repository """
        with open(compose_dataset_path(schema.id), "w") as fh:
            fh.write(schema.json())
    
    def _load_schema(self, schema_id) -> DatasetSchema:
        """ Load schema from schema repository """
        with open(compose_dataset_path(schema_id)) as fh:
            return DatasetSchema(json.load(fh))
    
    @property
    def _db_port(self):
        return postgres.PostgresPort(
            DB_URI
        )

    def handle_create_dataset(self, event: CreateDataset):
        schema = DatasetSchema.from_dict(event.schema)
        self._store_schema(schema)
        return DatasetCreated(
            id=schema.id
        )
    
    def handle_create_row(self, event: CreateRow):
        schema = self._load_schema(event.dataset_id)
        dclass = schema.get_table_by_id(event.dataset_table_id)
        dclass.validate(event.row)
        return RowCreated(
            dataset_id=schema.id,
            dataset_table_id=event.dataset_table_id,
            row=event.row
        )
    
    def handle_create_table(self, event: DatasetCreated):
        """ Creates a table when a dataset has been created """
        schema = self._load_schema(event.id)
        db = self._db_port
        db.create_schema(schema.id)
        for dataset_table in schema.tables:
            db_table = postgres.DBTable.from_dataset_table(
                schema.id, dataset_table
            )
            db.create_table(db_table)
        db.commit()
    
    def handle_insert_row(self, event: RowCreated):
        """ Insert the row into the dataclass table in db """
        schema = self._load_schema(event.dataset_id)
        db = self._db_port
        dataset_table = schema.get_table_by_id(event.dataset_table_id)
        table = postgres.DBTable.from_dataset_table(
            schema.id, dataset_table
        )
        db.insert_row(table, event.row)
        db.commit()

    def resolve(self, event: types.Event):
        result = self.registry[event.__class__](event)
        if isinstance(result, types.Event):
            self.resolve(result)
        return result
