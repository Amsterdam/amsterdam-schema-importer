from os import environ
import json
import csv
import io
from pathlib import Path

from pint import UnitRegistry
from pint.errors import UndefinedUnitError


# TODO: remove all flask dependencies
from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import request
from flask import current_app
from flask import render_template

from dataservices import amsterdam_schema as aschema


LAT_LON_SRID = 4326
DB_SRID = 28992


uri_path = environ["URI_PATH"]

ureg = UnitRegistry()




class Type(aschema.Dataset):
    ID_REF = "https://ams-schema.glitch.me/schema@v0.1#/definitions/id"
    URI_VERSION_PREFIX = "latest"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_names = {cls["id"]: self.primary_name(cls) for cls in self.classes}

    def primary_name(self, cls):
        id_fields = [
            k
            for k, v in cls["schema"]["properties"].items()
            if "$ref" in v and v["$ref"] == self.ID_REF
        ]
        return id_fields and id_fields[0] or None

    def _links(self, type_name, cls_name, id_=None):
        tail = "" if id_ is None else f"/{id_}"
        prefix = f"{uri_path}{self.URI_VERSION_PREFIX}"

        return {"href": f"{prefix}/{type_name}/{cls_name}{tail}"}

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
                ORDER BY geometry <-> ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s)
                """
            args = near + [srid_near_coords, DB_SRID, distance]
            return where_clause, args + args[:-1]

        def all_handler(where_clause, qargs):
            output_srid = DB_SRID if extension == "json" else LAT_LON_SRID

            sql = ""
            if extension == "csv":
                sql = f"SELECT *, ST_AsText(ST_Transform(geometry, {output_srid})) AS _geometry FROM {self.name}.{cls_name} {where_clause}"
            else:
                sql = f"SELECT *, ST_AsGeoJSON(ST_Transform(geometry, {output_srid})) AS _geometry FROM {self.name}.{cls_name} {where_clause}"

            result = current_app.db.con.execute(sql, qargs)

            result_rows = []
            for row in result:
                result_row = {}
                for k,v in dict(row).items():
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
                            "self": self._links(
                                self.name,
                                cls_name,
                                row[self.primary_names[cls_name].lower()],
                            )
                        },
                        "geometry": json.loads(row["geometry"]),
                    }
                    for row in result_rows
                ]
                return jsonify(rows)
            elif extension == "ndjson":
                rows = [
                    {
                        **dict(row),
                        "geometry": json.loads(row["geometry"])
                    }
                    for row in result_rows
                ]
                return ("\n").join(json.dumps(row, separators=(",", ":")) for row in rows)

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

        def handler():
            return all_handler(*fetch_clause_and_args())

        return handler

    def one(self, cls_name, extension="json"):
        def handler(cls_id):
            output_srid = DB_SRID if extension == "json" else LAT_LON_SRID
            primary_name = self.primary_names[cls_name]
            sql = f"""
                SELECT *, ST_AsGeoJSON(ST_Transform(geometry, {output_srid})) AS geometry FROM {self.name}.{cls_name}
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
                        "_links": {"self": self._links(self.name, cls_name, cls_id)},
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

