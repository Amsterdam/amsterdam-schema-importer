from pathlib import Path

from flask import abort
from flask import request
from flask import render_template
from flask_api import FlaskAPI
from flask_sacore import SACore


import json

app = FlaskAPI(__name__)

db = SACore("postgres://postgres:@postgres:5432/postgres", app)

ID_REF = "https://ams-schema.glitch.me/schema@v0.1#/definitions/id"
URI_VERSION_PREFIX = "latest"


class Class:
    def __init__(self, schema):
        self.properties = schema["properties"]
        id_fields = [
            k.lower()
            for k, v in self.properties.items()
            if "$ref" in v and v["$ref"] == ID_REF
        ]
        self.primary_name = id_fields and id_fields[0] or None


class Type:
    def __init__(self, schema):
        # set fields
        # set primary key
        # set all()  (class method)
        # set get(id)
        self.type_name = schema["id"]
        self.classes = {}
        for item in schema["items"]:
            class_name = item["id"]
            self.classes[class_name] = Class(item["schema"])

    def _links(self, type_name, cls_name, id_=None):
        tail = "" if id_ is None else f"/{id_}"

        return {"href": f"{request.host_url}{type_name}/{cls_name}{tail}"}

    def all(self, cls_name):
        def handler():
            sql = f"SELECT * FROM {self.type_name}.{cls_name}"
            result = db.con.execute(sql)
            rows = [
                {
                    **dict(row),
                    **{
                        "_links": {
                            "self": self._links(
                                self.type_name,
                                cls_name,
                                row[self.classes[cls_name].primary_name],
                            )
                        }
                    },
                }
                for row in result
            ]
            return dict(data=rows)

        return handler

    def one(self, cls_name):
        def handler(cls_id):
            primary_name = self.classes[cls_name].primary_name
            sql = f"SELECT * FROM {self.type_name}.{cls_name} WHERE {primary_name} = %s"
            rows = [dict(row) for row in db.con.execute(sql, (cls_id,))]
            if not rows:
                abort(404)
            return {
                **rows[0],
                **{"_links": {"self": self._links(self.type_name, cls_name, cls_id)}},
            }

        return handler


def make_spec(types):
    def spec():
        paths = {}
        for t in types:
            for cls_name, cls in t.classes.items():
                paths[f"/{t.type_name}/{cls_name}/{{cls_id}}"] = {
                    "get": {"parameters": [{"name": cls.primary_name, "in": "path"}]}
                }
                paths[f"/{t.type_name}/{cls_name}"] = {
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
        for cls_name, cls in t.classes.items():
            app.add_url_rule(
                f"/{prefix}/{t.type_name}/{cls_name}/<cls_id>",
                f"{t.type_name}_{cls_name}_id",
                t.one(cls_name),
            )
            app.add_url_rule(
                f"/{{prefix}/t.type_name}/{cls_name}",
                f"{t.type_name}_{cls_name}",
                t.all(cls_name),
            )
    app.add_url_rule("/spec", "openapi-spec", make_spec(types))


make_routes("/data")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    pass
