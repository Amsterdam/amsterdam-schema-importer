from os import environ
import json
from pathlib import Path

from pint import UnitRegistry
from pint.errors import UndefinedUnitError

from flask import abort
from flask import request
from flask import render_template
from flask_api import FlaskAPI
from flask_sacore import SACore

from dataservices import amsterdam_schema as aschema

LAT_LON_SRID = 4269
RD_SRID = 28992

app = FlaskAPI(__name__)

dsn = environ['DATABASE_URL']
routes_root_dir = environ['ROUTES_ROOT_DIR']
db = SACore(dsn, app)

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

        return {"href": f"{request.host_url}{type_name}/{cls_name}{tail}"}

    def all(self, cls_name):

        def fetch_clause_and_args():
            if "near" not in request.args.keys():
                return "WHERE 1 = 1", ()

            try:
                near = [float(a) for a in request.args.get("near").split(",")]
                distance = ureg.parse_expression(request.args.get("distance")).to(ureg.meter).magnitude
                rsid_near_coords = int(request.args.get("rsid", LAT_LON_SRID))
            except (ValueError, UndefinedUnitError):
                # XXX How specific should error messages be?
                abort(400)

            where_clause = f"""
                WHERE ST_DWithin(geometry, ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s), %s)
                """
            return where_clause, (near + [rsid_near_coords, RD_SRID, distance])

        def all_handler(where_clause, qargs):
            sql = f"SELECT * FROM {self.name}.{cls_name} {where_clause}"
            result = db.con.execute(sql, qargs)
            rows = [
                {
                    **dict(row),
                    **{
                        "_links": {
                            "self": self._links(
                                self.name, cls_name, row[self.primary_names[cls_name]]
                            )
                        }
                    },
                }
                for row in result
            ]
            return dict(data=rows)

        def handler():
            return all_handler(*fetch_clause_and_args())

        return handler

    def one(self, cls_name):
        def handler(cls_id):
            primary_name = self.primary_names[cls_name]
            sql = f"SELECT * FROM {self.name}.{cls_name} WHERE {primary_name} = %s"
            rows = [dict(row) for row in db.con.execute(sql, (cls_id,))]
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
        return {"openapi": "3.0.0", "paths": paths}

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
            app.add_url_rule(
                f"/{prefix}/{t.name}/{cls_name}/<cls_id>",
                f"{t.name}_{cls_name}_id",
                t.one(cls_name),
            )
            app.add_url_rule(
                f"/{prefix}/{t.name}/{cls_name}",
                f"{t.name}_{cls_name}",
                t.all(cls_name),
            )
    app.add_url_rule("/spec", "openapi-spec", make_spec(types))


make_routes(routes_root_dir)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    pass
