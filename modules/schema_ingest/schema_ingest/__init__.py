import json
from dataservices.amsterdam_schema import DatasetSchema


def schema_from_path(path):
    with open(path) as fh:
        return json.load(fh)


def load_schema(schema):
    return DatasetSchema(schema)


def main():
    path = "/home/jan/projects/amsterdam/amsterdam-schema-importer/data/bommen/bommen.dataset.schema.json"
    dsc = load_schema(schema_from_path(path))

    import pdb; pdb.set_trace()
