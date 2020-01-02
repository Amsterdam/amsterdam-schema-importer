import os
import json
from copy import deepcopy
import zipfile
import shapefile

amsterdam_schema_template = {
    "id": None,
    "type": "dataset",
    "title": "",
    "version": "0.0.1",
    "crs": "EPSG:28992",
    "tables": [],
}


table_template = {
    "id": None,
    "type": "table",
    "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "dataset", "type"],
        "properties": {
            "type": {
                "$ref": "https://schemas.data.amsterdam.nl/schema@v1.0#/definitions/class"
            },
            "dataset": {
                "$ref": "https://schemas.data.amsterdam.nl/schema@v1.0#/definitions/dataset"
            },
            "id": {
                "$ref": "https://schemas.data.amsterdam.nl/schema@v1.0#/definitions/id"
            },
        },
    },
}


shp_type_lookup = {"C": "string", "D": "string", "F": "number", "N": "number"}
format_lookup = {"D": "date-time"}


def convert_shapes_from_zip(shape_zip_path):
    with zipfile.ZipFile(shape_zip_path) as zf:
        schema = amsterdam_schema_template.copy()
        schema["id"] = shape_zip_path
        names = (os.path.splitext(n) for n in zf.namelist() if not n.startswith("__"))
        names = (name for name, ext in names if ext == ".shp")
        for name in names:
            with zf.open(f"{name}.shp") as shp, zf.open(f"{name}.dbf") as dbf:
                r = shapefile.Reader(shp=shp, dbf=dbf)
                properties = {}
                # Skip first DeleteFlag field (part of shp file)
                for field_name, field_type, _, _ in r.fields[1:]:
                    type_info = {"type": shp_type_lookup[field_type]}
                    if field_type in format_lookup:
                        type_info["format"] = format_lookup[field_type]
                    properties[field_name] = type_info
                # r.__geo_interface__
                table = deepcopy(table_template)
                table["id"] = name
                table["schema"]["properties"].update(properties)
                schema["tables"].append(table)
        return schema
