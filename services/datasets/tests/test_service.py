import json
from unittest import mock

import ndjson
import pytest

from datasets.service import (
    DatasetService, CreateDataset, DatasetCreated,
    InsertRow, DatasetSchema
)


@pytest.fixture
def dataset_dict():
    with open("tests/data/reclame/reclame.objects.ndjson") as fh:
        return ndjson.load(fh)


@pytest.fixture
def schema_dict():
    with open("tests/data/reclame/reclame.dataset.schema.json") as fh:
        return json.load(fh)


class MockedDatasetService(DatasetService):
    def _store_schema(self, schema): pass
    def _load_schema(self, schema_id):
        return mock.MagicMock(id=schema_id)


@pytest.fixture
def service():
    return MockedDatasetService()


@pytest.fixture
def created_dataset(service, schema_dict):
    event = CreateDataset(
        schema=schema_dict,
    )
    return service.create_dataset(event)


def test_create_dataset(created_dataset: DatasetCreated, schema_dict):
    assert created_dataset.id == schema_dict['id']


def test_insert_row(created_dataset: DatasetCreated,
                    service: DatasetService, dataset_dict: list):
    for row_dict in dataset_dict:
        event = InsertRow(
            dataset_id=created_dataset.id,
            row=row_dict
        )
        service.insert_row(event)