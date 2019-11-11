import json
from dataclasses import dataclass
from typing import Callable, Any

# abort: more specific Exception, handled in api.py
# db connection: pass in through the context
from pint import UnitRegistry
from pint.errors import UndefinedUnitError

from dynapi.domain.types import Resource, Collection
from .. import const

from ..exceptions import InvalidInputException, NotFoundException


ureg = UnitRegistry()


@dataclass
class SQLStrategy:
    collection: Collection
    db_con_factory: Callable[[None], Any]

    def fetch_near_clause_and_args(self, **filter_params):
        if "near" not in filter_params.keys():
            return "", ()

        try:
            near = [float(a) for a in filter_params.get("near").split(",")]
            distance = (
                ureg.parse_expression(filter_params.get("distance"))
                .to(ureg.meter)
                .magnitude
            )
            srid_near_coords = int(filter_params.get("srid", const.LAT_LON_SRID))
        except (ValueError, UndefinedUnitError):
            raise InvalidInputException()

        where_clause = f"""
            WHERE ST_DWithin(geometry, ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s), %s)
            ORDER BY geometry <-> ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s)
            """
        args = near + [srid_near_coords, const.DB_SRID, distance]
        return where_clause, args + args[:-1]

    def _fetch_rows(self, srid, geo_format, where_clause, qargs):
        transform_fie = "ST_AsText" if geo_format == "text" else "ST_AsGeoJSON"
        sql = f"""SELECT *, {transform_fie}(ST_Transform(geometry, {srid})) AS _geometry
                FROM {self.collection.catalog}.{self.collection.collection} {where_clause}"""
        rows = [dict(row) for row in self.db_con_factory().execute(sql, qargs)]

        if not rows:
            return []
        # Hmm, not easy to do this in an immutable chaining way
        for row in rows:
            tr = json.loads if geo_format == "geojson" else lambda x: x
            row["geometry"] = tr(row["_geometry"])
            del row["_geometry"]

        return [Resource(self.collection, row) for row in rows]

    def list(self, srid=const.DB_SRID, geo_format="geojson", **filter_params):
        where_clause, qargs = self.fetch_near_clause_and_args(**filter_params)
        return self._fetch_rows(srid, geo_format, where_clause, qargs)

    def get(self, document_id, srid=const.DB_SRID, geo_format="geojson"):
        where_clause, qargs = f" WHERE {self.collection.primary_name} = %s", [document_id]
        resources = self._fetch_rows(srid, geo_format, where_clause, qargs)
        if not resources:
            raise NotFoundException()
        return resources[0]


@dataclass
class EntityRepository:
    collection: Collection
    root_dir: str
    data_strategy: class

    def list(self, srid=const.DB_SRID, geo_format="geojson", **filter_params):
        return self.data_strategy.list(srid, geo_format, **filter_params)

    def get(self, document_id, srid=const.DB_SRID, geo_format="geojson"):
        return self.data_strategy.get(document_id, srid, geo_format)
