from os import environ
import functools
import csv
import io
from dataclasses import dataclass


from flask import Blueprint
from flask import jsonify
from flask import render_template


from dynapi import services
from . import const


LAT_LON_SRID = 4326
DB_SRID = 28992


api = Blueprint("v1", __name__)

routes_root_dir = environ["ROUTES_ROOT_DIR"]

ID_REF = "https://ams-schema.glitch.me/schema@v0.1#/definitions/id"
uri_path = environ["URI_PATH"]
URI_VERSION_PREFIX = "latest"


@dataclass
class Renderer:
    multiple: bool

    def _one_row(self, row):
        pass


class JSONRenderer(Renderer):

    def _one_row(self, row):
        return {**dict(row)}

    def __call__(self, content):
        if self.multiple:
            return jsonify([self._one_row(row) for row in content])
        return jsonify(self._one_row(content))


class CSVRenderer(Renderer):

    def __call__(self, content):
        # XXX fix when content is empty
        if not self.multiple:
            content = [content]
        mem_file = io.StringIO()
        writer = csv.writer(mem_file)
        writer.writerow(content[0].keys())
        writer.writerows([row.values() for row in content])
        return mem_file.getvalue()


class GeoJSONRenderer(Renderer):

    def _one_row(self, row):
        return {
            "type": "Feature",
            "id": row["id"],
            "properties": {
                k: v for k, v in dict(row).items() if k != "id"
            },
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


def get_renderer(extension, multiple):
    return {
        "json": JSONRenderer(multiple),
        "csv": CSVRenderer(multiple),
        "geojson": GeoJSONRenderer(multiple),
    }[extension]


def handler(catalog_service_method, multiple, **kwargs):
    srid = const.DB_SRID
    geo_format = "geojson"
    extension = kwargs.pop("extension", "json").lower()
    if extension == "csv":
        geo_format = "csv"
    if extension == "geojson":
        srid = const.LAT_LON_SRID
    renderer = get_renderer(extension, multiple)
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
        f"{prefix}/<catalog>/<collection>/<document_id>.<extension>",
        "get_document_with_extension",
        functools.partial(handler, catalog_service.get_document, False),
    )

    api.add_url_rule(
        f"{prefix}/<catalog>/<collection>",
        "get_collection",
        functools.partial(handler, catalog_service.list_resources, True),
    )

    api.add_url_rule(
        f"{prefix}/<catalog>/<collection>.<extension>",
        "get_collection_with_extension",
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
