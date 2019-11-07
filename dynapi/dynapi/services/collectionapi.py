from dataclasses import dataclass
from ..infra.db import EntityRepository
from .. import const


@dataclass
class CatalogContext:
    uri_path: str
    root_dir: str

    def entity_repo(self, catalog, collection):
        return EntityRepository(catalog, collection, self.uri_path, self.root_dir)


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
