import json
from unittest import mock

import ndjson
import pytest

from datasets.service import (
    DatasetService, CreateDataset, DatasetCreated,
    CreateRow, DatasetSchema
)


@pytest.fixture
def schema_dict():
    return {
        "id": "datasetid",
        "type": "dataset",
        "version": "0.0.1",
        "tables": [
            {
                "id": "tableid",
                "type": "table",
                "schema": {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "$id": "https://ams-schema.glitch.me/dataset/a/b",
                    "type": "object",
                    "required": [
                        "id",
                        "dataset",
                        "table"
                    ],
                    "properties": {
                        "id": {
                            "type": "string"
                        },
                        "table": {
                            "type": "string"
                        },
                        "dataset": {
                            "type": "string"
                        },
                        "value": {
                            "type": "integer"
                        }
                    }
                }
            }
        ]
    }


@pytest.fixture
def row_dict():
    return {
        "id": "someid",
        "table": "tableid",
        "dataset": "datasetid",
        "value": 123
    }


class MockedDatasetService(DatasetService):
    _temp_schema = None

    def _store_schema(self, schema):
        self._temp_schema = schema

    def _load_schema(self, _schema_id):
        return self._temp_schema
    
    @property
    def _db_port(self):
        return mock.MagicMock()


@pytest.fixture
def service():
    return MockedDatasetService()


@pytest.fixture
def created_dataset(service, schema_dict):
    event = CreateDataset(
        schema=schema_dict,
    )
    return service.resolve(event)


def test_create_dataset(created_dataset: DatasetCreated, schema_dict):
    assert created_dataset.id == schema_dict['id']


def test_insert_row(created_dataset: DatasetCreated, schema_dict,
                    service: DatasetService, row_dict: dict):
    event = CreateRow(
        dataset_id=row_dict['dataset'],
        dataset_table_id=row_dict['table'],
        row=row_dict
    )
    service.resolve(event)