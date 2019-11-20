from collections import UserDict
import json
import typing

import jsonschema

class DatasetSchema(UserDict):
    """ The schema of a dataset """
    @property
    def id(self):
        return self['id']

    @classmethod
    def from_dict(cls, obj: dict):
        """ Parses given dict and validates the given schema """
        return cls(obj)

    def json(self):
        return json.dumps(self.data)
    
    def validate(self, row):
        jsonschema.validate(row, self.data)


class Dataset(UserDict):
    """ The instance of a dataset """

    DEFAULT_CRS = "EPSG:28992"

    @classmethod
    def from_dict(cls, obj: dict, schema: DatasetSchema):
        """ Parses given dict and validates against the schema """
        return cls(obj)
    
    @classmethod
    def from_list(cls, objs: list, schema: DatasetSchema):
        dataset = cls(schema)
        dataset['classes'] = objs
        return dataset
    
    def validate(self, schema: DatasetSchema):
        jsonschema.validate(self, schema)

    @property
    def name(self):
        return self['id']

    @property
    def crs(self) -> str:
        return self.get('crs', self.DEFAULT_CRS)

    @property
    def classes(self) -> typing.List["Dataclass"]:
        return [
            Dataclass(i) for i in self['classes']
        ]
    
    def get_class_by_id(self, dataclass_id: str) -> "Dataclass":
        for dclass in self.classes:
            if dclass.id == dataclass_id:
                return dclass
        raise ValueError(f"Dataclass '{dataclass_id}' does not exist in {self}")


class Dataclass(UserDict):
    @property
    def id(self):
        return self['id']

    @property
    def fields(self):
        return [
            Field(i) for i in self['properties']
        ]


class Field(UserDict):
    @property
    def type(self):
        return self['type']