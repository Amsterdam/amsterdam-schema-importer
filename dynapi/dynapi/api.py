from os import environ
import json
import csv
import io
from pathlib import Path

from pint import UnitRegistry
from pint.errors import UndefinedUnitError

from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request
from flask import current_app
from flask import render_template


from dynapi import services
from dynapi.domain import types


LAT_LON_SRID = 4326
DB_SRID = 28992


api = Blueprint("v1", __name__)

routes_root_dir = environ["ROUTES_ROOT_DIR"]

ID_REF = "https://ams-schema.glitch.me/schema@v0.1#/definitions/id"
uri_path = environ["URI_PATH"]
URI_VERSION_PREFIX = "latest"
ureg = UnitRegistry()


def add_url_rule(app, url, name, func):
    try:
        app.add_url_rule(url, name, func)
    except AssertionError:
        pass

def make_routes(path):
    p = Path(path)
    prefix = f"/{URI_VERSION_PREFIX}"
    for schema_file in p.glob("**/*.schema.json"):
        schema = json.load(open(schema_file))
        t = types.Type(schema)
        for cls in t.classes:
            cls_name = cls["id"]
            api.add_url_rule(
                f"{prefix}/{t.name}/{cls_name}/<cls_id>.geojson",
                f"{t.name}_{cls_name}_id_geojson",
                t.one(cls_name, extension="geojson"),
            )
            api.add_url_rule(
                f"{prefix}/{t.name}/{cls_name}/<cls_id>",
                f"{t.name}_{cls_name}_id",
                t.one(cls_name),
            )
            api.add_url_rule(
                f"{prefix}/{t.name}/{cls_name}.geojson",
                f"{t.name}_{cls_name}_geojson",
                t.all(cls_name, extension="geojson"),
            )
            api.add_url_rule(
                f"{prefix}/{t.name}/{cls_name}.ndjson",
                f"{t.name}_{cls_name}_ndjson",
                t.all(cls_name, extension="ndjson"),
            )
            api.add_url_rule(
                f"{prefix}/{t.name}/{cls_name}.csv",
                f"{t.name}_{cls_name}_csv",
                t.all(cls_name, extension="csv"),
            )
            api.add_url_rule(
                f"{prefix}/{t.name}/{cls_name}",
                f"{t.name}_{cls_name}",
                t.all(cls_name),
            )
    oa_context = services.OpenAPIContext(
        uri_path, path, URI_VERSION_PREFIX
    )
    oa_service = services.OpenAPIService(oa_context)
    api.add_url_rule("/spec", "openapi-spec", oa_service.create_openapi_spec)


make_routes(routes_root_dir)


@api.route("/")
def index():
    openapi_spec_path = f"{uri_path}spec"
    return render_template("index.html", openapi_spec_path=openapi_spec_path)


@api.route("/recreate-routes")
def recreate_routes():

    return jsonify({"result": "ok"})


if __name__ == "__main__":
    pass
