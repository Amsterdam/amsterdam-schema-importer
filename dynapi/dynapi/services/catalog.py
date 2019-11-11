from dataclasses import dataclass
from typing import Callable, Any
from ..domain.types import Collection, CollectionRef
from ..infra.db import EntityRepository, SQLStrategy
from .. import const


@dataclass
class CatalogContext:
    root_dir: str
    db_con_factory: Callable[[None], Any]

    def entity_repo(self, catalog_str, collection_str):
        coll_ref= CollectionRef(catalog_str, collection_str)
        collection = Collection(coll_ref, self.root_dir)
        data_strategy = SQLStrategy(coll_ref, self.db_con_factory)
        return EntityRepository(
            collection, self.root_dir, data_strategy
        )


@dataclass
class CatalogService:
    context: CatalogContext

    def get_document(
        self,
        catalog: str,
        collection: str,
        document_id: str,
        srid: int = const.DB_SRID,
        geo_format: str = "geojson",
    ):
        return self.context.entity_repo(catalog, collection).get(
            document_id, srid=srid, geo_format=geo_format
        )

    def list_resources(
        self,
        catalog: str,
        collection: str,
        srid: int = const.DB_SRID,
        geo_format: str = "geojson",
        **filter_params
    ):
        return self.context.entity_repo(catalog, collection).list(
            srid=srid, geo_format=geo_format, **filter_params
        )
