from os import environ
import json
from pathlib import Path

from pint import UnitRegistry
from pint.errors import UndefinedUnitError

from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request
from flask import current_app
from flask import render_template

from dataservices import amsterdam_schema as aschema

# from .app import DynAPI

LAT_LON_SRID = 4269
RD_SRID = 28992


# app = DynAPI(__name__)
api = Blueprint("v1", __name__)

routes_root_dir = environ["ROUTES_ROOT_DIR"]

ID_REF = "https://ams-schema.glitch.me/schema@v0.1#/definitions/id"
URI_VERSION_PREFIX = "latest"
ureg = UnitRegistry()


class Type(aschema.Dataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_names = {cls["id"]: self.primary_name(cls) for cls in self.classes}

    def primary_name(self, cls):
        id_fields = [
            k.lower()
            for k, v in cls["schema"]["properties"].items()
            if "$ref" in v and v["$ref"] == ID_REF
        ]
        return id_fields and id_fields[0] or None

    def _links(self, type_name, cls_name, id_=None):
        tail = "" if id_ is None else f"/{id_}"
        prefix = URI_VERSION_PREFIX

        return {"href": f"{request.host_url}{prefix}/{type_name}/{cls_name}{tail}"}

    def all(self, cls_name, extension="json"):
        def fetch_clause_and_args():
            if "near" not in request.args.keys():
                return "WHERE 1 = 1", ()

            try:
                near = [float(a) for a in request.args.get("near").split(",")]
                distance = (
                    ureg.parse_expression(request.args.get("distance"))
                    .to(ureg.meter)
                    .magnitude
                )
                srid_near_coords = int(request.args.get("srid", LAT_LON_SRID))
            except (ValueError, UndefinedUnitError):
                # XXX How specific should error messages be?
                abort(400)

            where_clause = f"""
                WHERE ST_DWithin(geometry, ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s), %s)
                """
            return where_clause, (near + [srid_near_coords, RD_SRID, distance])

        def all_handler(where_clause, qargs):
            output_srid = RD_SRID if extension == "json" else LAT_LON_SRID
            sql = f"SELECT *, ST_AsGeoJSON(ST_Transform(geometry, {output_srid})) AS geometry FROM {self.name}.{cls_name} {where_clause}"
            result = current_app.db.con.execute(sql, qargs)

            if extension == "json":

                rows = [
                    {
                        **dict(row),
                        **{
                            "_links": {
                                "self": self._links(
                                    self.name,
                                    cls_name,
                                    row[self.primary_names[cls_name]],
                                )
                            }
                        },
                        **{"geometry": json.loads(row["geometry"])},
                    }
                    for row in result
                ]
                return jsonify(rows)

            elif extension == "geojson":

                geojson = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "id": row["id"],
                            "properties": {
                                k: v
                                for k, v in dict(row).items()
                                if k not in set(["geometry", "id"])
                            },
                            **{"geometry": json.loads(row["geometry"])},
                        }
                        for row in result
                    ],
                }
                return jsonify(geojson)

            else:
                abort(400)

        def handler():
            return all_handler(*fetch_clause_and_args())

        return handler

    def one(self, cls_name):
        def handler(cls_id):
            primary_name = self.primary_names[cls_name]
            sql = f"SELECT * FROM {self.name}.{cls_name} WHERE {primary_name} = %s"
            rows = [dict(row) for row in current_app.db.con.execute(sql, (cls_id,))]
            if not rows:
                abort(404)
            return {
                **rows[0],
                **{"_links": {"self": self._links(self.name, cls_name, cls_id)}},
            }

        return handler


def make_spec(types):
    def spec():
        paths = {}
        prefix = URI_VERSION_PREFIX
        for t in types:
            for cls in t.classes:
                cls_name = cls["id"]
                primary_name = t.primary_names[cls_name]
                paths[f"/{prefix}/{t.name}/{cls_name}/{{cls_id}}"] = {
                    "get": {"parameters": [{"name": primary_name, "in": "path"}]}
                }
                paths[f"/{prefix}/{t.name}/{cls_name}"] = {
                    "get": {"description": "Get all"}
                }
        return jsonify({"openapi": "3.0.0", "paths": paths})

    return spec


def make_routes(path):
    p = Path(path)
    prefix = URI_VERSION_PREFIX
    types = []
    for schema_file in p.glob("**/*.schema.json"):
        schema = json.load(open(schema_file))
        t = Type(schema)
        types.append(t)
        for cls in t.classes:
            cls_name = cls["id"]
            api.add_url_rule(
                f"/{prefix}/{t.name}/{cls_name}/<cls_id>",
                f"{t.name}_{cls_name}_id",
                t.one(cls_name),
            )
            api.add_url_rule(
                f"/{prefix}/{t.name}/{cls_name}.geojson",
                f"{t.name}_{cls_name}_geojson",
                t.all(cls_name, extension="geojson"),
            )
            api.add_url_rule(
                f"/{prefix}/{t.name}/{cls_name}",
                f"{t.name}_{cls_name}",
                t.all(cls_name),
            )
    api.add_url_rule("/spec", "openapi-spec", make_spec(types))


make_routes(routes_root_dir)


@api.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    pass
