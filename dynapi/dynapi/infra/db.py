import json
from dataclasses import dataclass
from dataclasses import field
from typing import List

from flask import request
from flask import current_app
from flask import abort
from pint import UnitRegistry
from pint.errors import UndefinedUnitError

from dynapi.domain.types import Resource, fetch_class_info
from .. import const


ureg = UnitRegistry()


@dataclass
class EntityRepository:
    catalog: str
    collection: str
    root_dir: str
    primary_name: str = None
    properties: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.primary_name, self.properties = fetch_class_info(
            self.root_dir, self.catalog, self.collection
        )

    def fetch_near_clause_and_args(self):
        if "near" not in request.args.keys():
            return "", ()

        try:
            near = [float(a) for a in request.args.get("near").split(",")]
            distance = (
                ureg.parse_expression(request.args.get("distance"))
                .to(ureg.meter)
                .magnitude
            )
            srid_near_coords = int(request.args.get("srid", const.LAT_LON_SRID))
        except (ValueError, UndefinedUnitError):
            # XXX How specific should error messages be?
            abort(400)

        where_clause = f"""
            WHERE ST_DWithin(geometry, ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s), %s)
            ORDER BY geometry <-> ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s)
            """
        args = near + [srid_near_coords, const.DB_SRID, distance]
        return where_clause, args + args[:-1]

    def _fetch_rows(self, srid, geo_format, where_clause, qargs):
        transform_fie = "ST_AsText" if geo_format == "text" else "ST_AsGeoJSON"
        sql = f"""SELECT *, {transform_fie}(ST_Transform(geometry, {srid})) AS _geometry
                FROM {self.catalog}.{self.collection} {where_clause}"""
        rows = [dict(row) for row in current_app.db.con.execute(sql, qargs)]

        if not rows:
            return []
        # Hmm, not easy to do this in an immutable chaining way
        for row in rows:
            tr = json.loads if geo_format == "geojson" else lambda x: x
            row["geometry"] = tr(row["_geometry"])
            del row["_geometry"]

        return [
            Resource(
                self.catalog, self.collection, self.primary_name, row, self.properties
            )
            for row in rows
        ]

    def list(self, srid=const.DB_SRID, geo_format="geojson", **filter_params):
        where_clause, qargs = self.fetch_near_clause_and_args()
        return self._fetch_rows(srid, geo_format, where_clause, qargs)

    def get(self, document_id, srid=const.DB_SRID, geo_format="geojson"):
        where_clause, qargs = f" WHERE {self.primary_name} = %s", [document_id]
        rows = self._fetch_rows(srid, geo_format, where_clause, qargs)
        if not rows:
            abort(404)  # XXX Do this here, or better in api.py?
        return Resource(
            self.catalog, self.collection, self.primary_name, rows[0], self.properties
        )
