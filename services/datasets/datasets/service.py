import json
import os

from dataclasses import dataclass
from dataservices.amsterdam_schema import Dataset, DatasetSchema

from .core import types

DATASETS_PATH = os.getenv("DATASET_PATH", "./data")

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
class InsertRow(types.Event):
    """ Inserts a document into """
    dataset_id: str
    row: dict


@dataclass
class RowInserted(types.Event):
    """ Fact of an inserted row """
    dataset_id: str
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
    def _store_schema(self, schema: DatasetSchema):
        """ Store schema in schema repository """
        with open(compose_dataset_path(schema.id), "w") as fh:
            fh.write(schema.json())
    
    def _load_schema(self, schema_id):
        """ Load schema from schema repository """
        with open(compose_dataset_path(schema_id)) as fh:
            return DatasetSchema(json.load(fh))

    def create_dataset(self, event: CreateDataset):
        schema = DatasetSchema.from_dict(event.schema)
        self._store_schema(schema)
        return DatasetCreated(
            id=schema.id
        )
    
    def insert_row(self, event: InsertRow):
        schema = self._load_schema(event.dataset_id)
        schema.validate(event.row)
        return RowInserted(
            dataset_id=schema.id,
            row_id="someid"
        )
