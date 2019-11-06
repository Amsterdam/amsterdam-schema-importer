from os import environ
import functools
import csv
import io
import json
from dataclasses import dataclass


from flask import Blueprint
from flask import jsonify
from flask import request
from flask import render_template
from flask import Response


from dynapi import services
from . import const


api = Blueprint("v1", __name__)

routes_root_dir = environ["ROUTES_ROOT_DIR"]

uri_path = environ["URI_PATH"]
URI_VERSION_PREFIX = "latest"


@dataclass
class Renderer:
    multiple: bool

    def _one_row(self, row):
        pass


class JSONRenderer(Renderer):
    def _one_row(self, row):
        return {**row}

    def __call__(self, content):
        if self.multiple:
            return jsonify([self._one_row(row) for row in content])
        return jsonify(self._one_row(content))


class NDJSONRenderer(Renderer):
    def _one_row(self, row):
        return json.dumps(row, separators=(",", ":"))

    def __call__(self, content):
        if self.multiple:
            response_content = "\n".join([self._one_row(row) for row in content])
        else:
            response_content = self._one_row(content)
        return Response(response_content, mimetype="application/x-ndjson")


class CSVRenderer(Renderer):
    def __call__(self, content):
        # XXX fix when content is empty
        if not self.multiple:
            content = [content]
        mem_file = io.StringIO()
        writer = csv.writer(mem_file)
        writer.writerow(content[0].keys())
        writer.writerows([row.values() for row in content])

        return Response(
            mem_file.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=output.csv"},
        )


class GeoJSONRenderer(Renderer):
    def _one_row(self, row):
        return {
            "type": "Feature",
            "id": row["id"],
            "properties": {k: v for k, v in row.items() if k != "id"},
        }

    def __call__(self, content):
        # XXX add header for crs coord system
        if not self.multiple:
            return jsonify(self._one_row(content))

        return jsonify(
            {
                "type": "FeatureCollection",
                "features": [self._one_row(row) for row in content],
            }
        )


def get_renderer(content_type, multiple):
    return {
        "application/json": JSONRenderer(multiple),
        "applicatio/ndjson": NDJSONRenderer(multiple),
        "text/csv": CSVRenderer(multiple),
        "application/geojson": GeoJSONRenderer(multiple),
    }.get(content_type, JSONRenderer(multiple))


def handler(catalog_service_method, multiple, **kwargs):
    srid = const.DB_SRID
    geo_format = "geojson"

    content_type = request.headers.get("Accept", "application/json")
    content_type = request.args.get("content-type", content_type)

    if content_type == "text/csv":
        geo_format = "csv"
    if content_type == "application/geojson":
        srid = const.LAT_LON_SRID
    renderer = get_renderer(content_type, multiple)
    return renderer(catalog_service_method(srid=srid, geo_format=geo_format, **kwargs))


def make_routes(path):
    prefix = f"/{URI_VERSION_PREFIX}"

    catalog_context = services.CatalogContext(uri_path, path, URI_VERSION_PREFIX)
    catalog_service = services.CatalogService(catalog_context)

    api.add_url_rule(
        f"{prefix}/<catalog>/<collection>/<document_id>",
        "get_document",
        functools.partial(handler, catalog_service.get_document, False),
    )

    api.add_url_rule(
        f"{prefix}/<catalog>/<collection>",
        "get_collection",
        functools.partial(handler, catalog_service.list_resources, True),
    )

    oa_context = services.OpenAPIContext(uri_path, path, URI_VERSION_PREFIX)
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
