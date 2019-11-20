from dataclasses import dataclass
from typing import Any

# abort: more specific Exception, handled in api.py
# db connection: pass in through the context

from dynapi.domain.types import Resource, Collection
from .. import const


@dataclass
class EntityRepository:
    collection: Collection
    data_strategy: Any

    def list(self, srid=const.DB_SRID, geo_format="geojson", **filter_params):
        return [
            Resource(self.collection, row)
            for row in self.data_strategy.list(srid, geo_format, **filter_params)
        ]

    def get(self, document_id, srid=const.DB_SRID, geo_format="geojson"):
        return Resource(
            self.collection,
            self.data_strategy.get(
                document_id, self.collection.primary_name, srid, geo_format
            ),
        )
