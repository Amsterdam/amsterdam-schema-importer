from collections import UserDict
from dataclasses import dataclass
import json
import typing

import jsonschema
import requests

from . import refs


class SchemaType(UserDict):
    @property
    def id(self):
        return self["id"]

    @property
    def type(self):
        return self["type"]

    def json(self):
        return json.dumps(self.data)


class DatasetType(UserDict):
    pass


class DatasetSchema(SchemaType):
    """ The schema of a dataset """

    @classmethod
    def from_dict(cls, obj: dict):
        """ Parses given dict and validates the given schema """
        # XXX validation not added yet
        return cls(obj)

    @property
    def tables(self) -> typing.List["DatasetTableSchema"]:
        return [DatasetTableSchema(i) for i in self["tables"]]

    def get_table_by_id(self, table_id: str) -> "DatasetTableSchema":
        for table in self.tables:
            if table.id == table_id:
                return table
        raise ValueError(f"Schema of table '{table_id}' does not exist in {self}")


class DatasetTableSchema(SchemaType):
    """ The class within a dataset """

    @property
    def fields(self):
        return [
            DatasetFieldSchema(name=name, type=self.resolve(spec))
            for name, spec in self["schema"]["properties"].items()
        ]

    def validate(self, row: dict):
        jsonschema.validate(row, self.data["schema"])

    def resolve(self, spec):
        # when $ref, ignore everything else
        if "$ref" in spec:
            type_ = spec["$ref"]
            if type_ not in refs.REFS:
                raise jsonschema.exceptions.ValidationError(f"Unknown: {spec['$ref']}")
            return type_
        return spec["type"]


@dataclass
class DatasetFieldSchema:
    """ A field in a dataclass """

    name: str
    type: str


class DatasetRow(DatasetType):
    """ An actual instance of data """

    def validate(self, schema: DatasetSchema):
        table = schema.get_table_by_id(self["table"])
        table.validate(self.data)


def schema_def_from_path(schema_path):
    with open(schema_path) as fh:
        return json.load(fh)


def schema_defs_from_url(schemas_url):
    schema_lookup = {}
    response = requests.get(schemas_url)
    response.raise_for_status()
    for schema_dir_info in response.json():
        schema_dir_name = schema_dir_info["name"]
        response = requests.get(f"{schemas_url}{schema_dir_name}/")
        response.raise_for_status()
        for schema_file_info in response.json():
            schema_name = schema_file_info["name"]
            response = requests.get(f"{schemas_url}{schema_dir_name}/{schema_name}")
            response.raise_for_status()
            schema_lookup[schema_name] = response.json()
    return schema_lookup


def schema_def_from_url(schemas_url, schema_name):
    return schema_defs_from_url(schemas_url)[schema_name]


def fetch_schema(schema_def):
    return DatasetSchema(schema_def)
