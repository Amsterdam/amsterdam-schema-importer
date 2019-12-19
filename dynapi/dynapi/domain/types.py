import os
from dataservices import amsterdam_schema as aschema
from dataclasses import dataclass
from dataclasses import field
from dataclasses import make_dataclass
from dataclasses import InitVar

from typing import List, Any

from schema_ingest import schema_def_from_url

SCHEMA_URL = os.getenv("SCHEMA_URL")

class Type(aschema.DatasetSchema):
    ID_REF = "https://schemas.data.amsterdam.nl/schema@v1.0#/definitions/id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_names = {table["id"]: self.primary_name(table) for table in self.tables}

    def primary_name(self, table):
        id_fields = [
            k
            for k, v in table["schema"]["properties"].items()
            if "$ref" in v and v["$ref"] == self.ID_REF
        ]
        return id_fields and id_fields[0] or None

    @classmethod
    def fetch_class_info(cls, root_dir: str, catalog: str, collection: str):
        schema = schema_def_from_url(SCHEMA_URL, catalog, collection)
        type_ = cls(schema)
        primary_name = type_.primary_names[collection]
        properties = [k for k in type_.get_table_by_id(collection)["schema"]["properties"].keys()]
        return primary_name, properties


@dataclass
class CollectionRef:
    catalog: str
    collection: str


@dataclass
class Collection:
    coll_ref: CollectionRef
    root_dir: str
    primary_name: str = None
    properties: List[Any] = field(default_factory=list)

    def __post_init__(self):
        self.primary_name, self.properties = Type.fetch_class_info(
            self.root_dir, self.coll_ref.catalog, self.coll_ref.collection
        )


@dataclass
class Resource:
    collection: Collection
    row: InitVar[Any] = None

    def __post_init__(self, row):
        properties = self.collection.properties
        fields_class = make_dataclass('Fields', properties)
        self.fields = fields_class(
            **{k: v for k, v in row.items() if k in set(properties)}
        )
