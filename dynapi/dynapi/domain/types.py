from dataservices import amsterdam_schema as aschema
from dataclasses import dataclass
from dataclasses import field
from dataclasses import make_dataclass
from dataclasses import InitVar

from typing import List, Any

from dynapi.lib import get_datasets


class Type(aschema.Dataset):
    ID_REF = "https://ams-schema.glitch.me/schema@v0.1#/definitions/id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_names = {cls["id"]: self.primary_name(cls) for cls in self.classes}

    def primary_name(self, cls):
        id_fields = [
            k
            for k, v in cls["schema"]["properties"].items()
            if "$ref" in v and v["$ref"] == self.ID_REF
        ]
        return id_fields and id_fields[0] or None

    @classmethod
    def fetch_class_info(cls, root_dir: str, catalog: str, collection: str):
        current_type = current_cls = None

        properties = []
        types = (cls(schema) for schema in get_datasets(root_dir))
        for t in types:
            if t.name == catalog:
                current_type = t
                for tcls in t.classes:
                    if tcls["id"] == collection:
                        current_cls = tcls
                        # XXX excluding class/datasets should not be hardcoded
                        properties = [
                            k
                            for k in tcls["schema"]["properties"].keys()
                            if k not in set(["class", "dataset"])
                        ]
        primary_name = current_type.primary_name(current_cls)
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
