"""
Service for generating an OpenAPI spec
"""
from dataclasses import dataclass
import typing

from dynapi.lib import get_datasets
from dynapi.domain.types import Type


@dataclass
class OpenAPIContext:
    uri_path: str
    root_dir: str
    uri_version_prefix: st

    def compose_uri(self, type_name, class_name, *class_params):
        return  "/".join([
            self.uri_path + self.uri_version_prefix,
            type_name, class_name
        ] + list(class_params))

    
    def entity_repo(self, catalog,  collection):
        return EntityRepository(catalog, collection)


@dataclass
class OpenAPIService:
    context: OpenAPIContext

    def _get_types(self) -> typing.Iterator[Type]:
        return map(
            Type, get_datasets(self.context.root_dir)
        )
    
    def create_openapi_spec(self):
        paths = {}
        info = {"title": "OpenAPI Amsterdam Schema", "version": "0.0.1"}
        for t in self._get_types():
            for cls in t.classes:
                cls_name = cls["id"]
                primary_name = t.primary_names[cls_name]
                primary_name_description = cls["schema"]["properties"][primary_name][
                    "description"
                ]
                paths[
                    self.context.compose_uri(t.name, cls_name, "{cls_id}")
                ] = { 
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
                paths[
                    self.context.compose_uri(t.name, cls_name)
                ] = {
                    "get": {"description": t["title"]}
                }
        return {
            "openapi": "3.0.0", "paths": paths, "info": info
        }

    def get_document(self, catalog: str, collection: str, document_id: str):
        self.context.repo(catalog, collection).get(document_id)

    def list_resources(self, collection: str, **filter_params):
        self.context.repo(collection).list(**filter_params)