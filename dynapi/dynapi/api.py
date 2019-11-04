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

from dataservices import amsterdam_schema as aschema

LAT_LON_SRID = 4326
DB_SRID = 28992


api = Blueprint("v1", __name__)

routes_root_dir = environ["ROUTES_ROOT_DIR"]

ID_REF = "https://ams-schema.glitch.me/schema@v0.1#/definitions/id"
uri_path = environ["URI_PATH"]
URI_VERSION_PREFIX = "latest"
ureg = UnitRegistry()

# XXX hmm, module level var. Maybe we need a central type reg, e.g. in Redis?
_type_reg = {}


class Type(aschema.Dataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_names = {cls["id"]: self.primary_name(cls) for cls in self.classes}

    def primary_name(self, cls):
        id_fields = [
            k
            for k, v in cls["schema"]["properties"].items()
            if "$ref" in v and v["$ref"] == ID_REF
        ]
        return id_fields and id_fields[0] or None

    @classmethod
    def _fetch_type_from_name(cls, type_name):
        global _type_reg
        try:
            return _type_reg[type_name]
        except KeyError:
            abort(404)

    @classmethod
    def _links(cls, type_name, cls_name, id_=None):
        tail = "" if id_ is None else f"/{id_}"
        prefix = f"{uri_path}{URI_VERSION_PREFIX}"

        return {"href": f"{prefix}/{type_name}/{cls_name}{tail}"}

    @classmethod
    def all(cls):
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
                ORDER BY geometry <-> ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s)
                """
            args = near + [srid_near_coords, DB_SRID, distance]
            return where_clause, args + args[:-1]

        def all_handler(type_name, class_name, where_clause, qargs, extension="jsoin"):
            output_srid = DB_SRID if extension == "json" else LAT_LON_SRID
            type_ = cls._fetch_type_from_name(type_name)

            sql = ""
            if extension == "csv":
                sql = f"SELECT *, ST_AsText(ST_Transform(geometry, {output_srid})) AS _geometry FROM {type_name}.{class_name} {where_clause}"
            else:
                sql = f"SELECT *, ST_AsGeoJSON(ST_Transform(geometry, {output_srid})) AS _geometry FROM {type_name}.{class_name} {where_clause}"

            result = current_app.db.con.execute(sql, qargs)

            result_rows = []
            for row in result:
                result_row = {}
                for k, v in dict(row).items():
                    if k == "geometry":
                        v = row["_geometry"]
                    elif k == "_geometry":
                        continue
                    result_row[k] = v
                result_rows.append(result_row)

            if extension == "json":
                rows = [
                    {
                        **dict(row),
                        "_links": {
                            "self": cls._links(
                                type_name,
                                class_name,
                                row[type_.primary_names[class_name].lower()],
                            )
                        },
                        "geometry": json.loads(row["geometry"]),
                    }
                    for row in result_rows
                ]
                return jsonify(rows)
            elif extension == "ndjson":
                rows = [
                    {**dict(row), "geometry": json.loads(row["geometry"])}
                    for row in result_rows
                ]
                return ("\n").join(
                    json.dumps(row, separators=(",", ":")) for row in rows
                )

            elif extension == "csv":
                rows = result_rows
                mem_file = io.StringIO()
                writer = csv.writer(mem_file)
                writer.writerow(rows[0].keys())
                writer.writerows([row.values() for row in rows])
                return mem_file.getvalue()

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
                            "geometry": json.loads(row["geometry"]),
                        }
                        for row in result_rows
                    ],
                }
                return jsonify(geojson)

            else:
                abort(400)

        def handler(type_name, class_name, extension="json"):
            return all_handler(
                type_name, class_name, *fetch_clause_and_args(), extension
            )

        return handler

    @classmethod
    def one(cls):
        def handler(type_name, class_name, cls_id, extension="json"):
            output_srid = DB_SRID if extension == "json" else LAT_LON_SRID
            type_ = cls._fetch_type_from_name(type_name)
            primary_name = type_.primary_names[class_name]
            sql = f"""
                SELECT *, ST_AsGeoJSON(ST_Transform(geometry, {output_srid})) AS geometry FROM {type_name}.{class_name}
                    WHERE {primary_name} = %s
            """
            rows = [dict(row) for row in current_app.db.con.execute(sql, (cls_id,))]
            if not rows:
                abort(404)
            row = rows[0]
            if extension == "json":
                return jsonify(
                    {
                        **row,
                        "_links": {"self": cls._links(type_name, class_name, cls_id)},
                        "geometry": json.loads(row["geometry"]),
                    }
                )
            elif extension == "geojson":
                return jsonify(
                    {
                        "type": "Feature",
                        "id": row["id"],
                        "properties": {
                            k: v
                            for k, v in dict(row).items()
                            if k not in set(["geometry", "id"])
                        },
                        "geometry": json.loads(row["geometry"]),
                    }
                )
            else:
                abort(400)

        return handler


def make_spec(types):
    def spec():
        paths = {}
        prefix = f"{uri_path}{URI_VERSION_PREFIX}"
        info = {"title": "OpenAPI Amsterdam Schema", "version": "0.0.1"}
        for t in types:
            for cls in t.classes:
                cls_name = cls["id"]
                primary_name = t.primary_names[cls_name]
                primary_name_description = cls["schema"]["properties"][primary_name][
                    "description"
                ]
                paths[f"{prefix}/{t.name}/{cls_name}/{{cls_id}}"] = {
                    "get": {
                        "parameters": [
                            {
                                "name": primary_name,
                                "in": "path",
                                "required": True,
                                "description": primary_name_description,
                            }
                        ]
                    }
                }
                paths[f"{prefix}/{t.name}/{cls_name}"] = {
                    "get": {"description": t["title"]}
                }
        return jsonify({"openapi": "3.0.0", "paths": paths, "info": info})

    return spec


def fetch_types():
    global _type_reg
    _type_reg = {}
    p = Path(routes_root_dir)
    types = []
    for schema_file in p.glob("**/*.schema.json"):
        schema = json.load(open(schema_file))
        t = Type(schema)
        types.append(t)
        _type_reg[t.name] = t


@api.route("/refresh-types")
def refresh_types():
    fetch_types()
    return jsonify({"result": "ok"})


def make_routes():

    fetch_types()
    prefix = f"/{URI_VERSION_PREFIX}"

    types = _type_reg.values()
    for t in types:
        api.add_url_rule(
            f"{prefix}/<type_name>/<class_name>/<cls_id>.<extension>",
            "one_handler_ext",
            Type.one(),
        )
        api.add_url_rule(
            f"{prefix}/<type_name>/<class_name>/<cls_id>", f"one_handler", Type.one()
        )
        api.add_url_rule(
            f"{prefix}/<type_name>/<class_name>.<extension>",
            "all_handler_ext",
            Type.all(),
        )
        api.add_url_rule(
            f"{prefix}/<type_name>/<class_name>", "all_handler", Type.all()
        )
    api.add_url_rule("/spec", "openapi-spec", make_spec(types))


make_routes()


@api.route("/")
def index():
    openapi_spec_path = f"{uri_path}spec"
    return render_template("index.html", openapi_spec_path=openapi_spec_path)


if __name__ == "__main__":
    pass
