from dataclasses import dataclass
from ..infra.db import EntityRepository
from dynapi.lib import get_datasets
from dynapi.domain.types import Type
from .. import const


@dataclass
class CatalogContext:
    uri_path: str
    root_dir: str
    uri_version_prefix: str

    def get_self_link(self, catalog, collection, document_id):
        return f"/{self.uri_path}/{self.uri_version_prefix}/{catalog}/{collection}/{document_id}"

    def entity_repo(self, catalog, collection):
        return EntityRepository(catalog, collection, self.root_dir)


@dataclass
class CatalogService:
    context: CatalogContext

    def _get_primary_map(self):
        types = (Type(schema) for schema in get_datasets(self.context.root_dir))
        return {t.name: t.primary_names for t in types}

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
