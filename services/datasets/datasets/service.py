import json
import os

from dataclasses import dataclass
from dataservices.amsterdam_schema import Dataset, DatasetSchema

from .core import types
from .ports import postgres

DATASETS_PATH = os.getenv("DATASET_PATH", "./data")
DB_URI os.getenv(
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
    dataclass_id: str
    row: dict


@dataclass
class RowCreated(types.Event):
    """ Fact of an inserted row """
    dataset_id: str
    dataclass_id: str
    row_id: str


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
        self.registry = dict(
            [
                (f.__annotations__['event'], f) for
                name, f in self.__dict__.items() if f.startswith("handle_")
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
        schema.validate(event.row)
        return RowInserted(
            dataset_id=schema.id,
            dataclass_id=event.dataclass_id,
            row=event.row
        )
    
    def handle_create_table(self, event: DatasetCreated):
        """ Creates a table when a dataset has been created """
        schema = self._load_schema(event.schema_id)
        db = self._db_port
        for dclass in schema.classes:
            table = postgres.DatasetTable.from_dataclass(
                schema.id, dclass
            )
            db.create_table(table)
        db.commit()
    
    def handle_insert_row(self, event: RowCreated):
        """ Insert the row into the dataclass table in db """
        schema = self._load_schema(event.schema_id)
        db = self._db_port
        dclass = schema.get_class_by_id(event.dataclass_id)
        table = postgres.DatasetTable.from_dataclass(
            schema.id, dclass
        )
        db.insert_row(table, event.row)

    def resolve(self, event: types.Event):
        result = self.registry[event.__class__](event)
        if isinstance(result, types.Event):
            self.resolve(result)
        return result

