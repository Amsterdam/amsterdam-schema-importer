import os
import functools
import csv
import io
import json
from dataclasses import dataclass
from dataclasses import asdict


from flask import Blueprint
from flask import jsonify
from flask import request
from flask import current_app
from flask import render_template
from flask import abort
from flask import Response


from dynapi import services
from . import const

from .exceptions import InvalidInputException, NotFoundException


api = Blueprint("v1", __name__)

SCHEMA_URL = os.getenv("SCHEMA_URL")

uri_path_prefix = os.getenv("URI_PATH_PREFIX")


# XXX instead of explicitly stating multiple
# we could also check in the renderer if the content is iterable
@dataclass
class Renderer:
    multiple: bool

    def render(self, resource):
        pass


class JSONRenderer(Renderer):
    def get_self_link(self, resource):
        document_id = getattr(resource.fields, resource.collection.primary_name)
        return (
            f"{uri_path_prefix}{resource.collection.coll_ref.catalog}/"
            f"{resource.collection.coll_ref.collection}/{document_id}"
        )

    def render(self, resource):

        rendered = asdict(resource.fields)
        rendered["_links"] = {"self": {"href": self.get_self_link(resource)}}
        return rendered

    def __call__(self, content):
        if self.multiple:
            return jsonify([self.render(resource) for resource in content])
        return jsonify(self.render(content))


class NDJSONRenderer(Renderer):
    def render(self, resource):
        return json.dumps(asdict(resource.fields), separators=(",", ":"))

    def __call__(self, content):
        if self.multiple:
            response_content = "\n".join(
                [self.render(resource) for resource in content]
            )
        else:
            response_content = self.render(content)
        return Response(response_content, mimetype="application/x-ndjson")


class CSVRenderer(Renderer):
    def __call__(self, content):
        # XXX fix when content is empty
        if not self.multiple:
            content = [asdict(content.fields)]
        else:
            content = [asdict(r.fields) for r in content]
        mem_file = io.StringIO()
        writer = csv.writer(mem_file)
        writer.writerow(content[0].keys())
        writer.writerows([d.values() for d in content])

        return Response(
            mem_file.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=output.csv"},
        )


class GeoJSONRenderer(Renderer):
    def render(self, resource):
        resource = asdict(resource.fields)
        return {
            "type": "Feature",
            "id": resource["id"],
            "properties": {k: v for k, v in resource.items() if k != "id"},
        }

    def __call__(self, content):
        # For NL-API compliance add Content-Crs header
        if not self.multiple:
            response = jsonify(self.render(content))
        else:
            response = jsonify(
                {
                    "type": "FeatureCollection",
                    "features": [self.render(resource) for resource in content],
                }
            )
        response.headers["Content-Crs"] = "EPSG:4326"
        return response


def get_renderer(content_type, multiple):
    # XXX 7.2.10 API-25: Check the Content-Type header settings
    # Check the Content-Type header is application/json or another supported
    # content types, otherwise send the HTTP status code 415 Unsupported Media Type.
    return {
        "application/json": JSONRenderer(multiple),
        "application/ndjson": NDJSONRenderer(multiple),
        "text/csv": CSVRenderer(multiple),
        "application/geojson": GeoJSONRenderer(multiple),
    }.get(content_type, JSONRenderer(multiple))


def handler(catalog_service_method, multiple, **kwargs):
    srid = const.DB_SRID
    geo_format = "geojson"

    content_type = request.headers.get("Accept", "application/json")
    content_type = request.args.get("content-type", content_type)
    filter_params = {**kwargs, **request.args}

    if content_type == "text/csv":
        geo_format = "csv"
    if content_type == "application/geojson":
        srid = const.LAT_LON_SRID
    renderer = get_renderer(content_type, multiple)
    try:
        return renderer(
            catalog_service_method(srid=srid, geo_format=geo_format, **filter_params)
        )
    except InvalidInputException:
        abort(400)
    except NotFoundException:
        abort(404)


def db_con_factory():
    return current_app.db.con


def make_routes(schema_url):

    catalog_context = services.CatalogContext(schema_url, db_con_factory)
    catalog_service = services.CatalogService(catalog_context)

    api.add_url_rule(
        f"/<catalog>/<collection>/<document_id>",
        "get_document",
        functools.partial(handler, catalog_service.get_document, False),
    )

    api.add_url_rule(
        f"/<catalog>/<collection>",
        "get_collection",
        functools.partial(handler, catalog_service.list_resources, True),
    )

    oa_context = services.OpenAPIContext(uri_path_prefix, schema_url)
    oa_service = services.OpenAPIService(oa_context)
    api.add_url_rule("/spec", "openapi-spec", oa_service.create_openapi_spec)


make_routes(SCHEMA_URL)


@api.route("/")
def index():
    openapi_spec_path = f"./spec"
    return render_template("index.html", openapi_spec_path=openapi_spec_path)


if __name__ == "__main__":
    pass
