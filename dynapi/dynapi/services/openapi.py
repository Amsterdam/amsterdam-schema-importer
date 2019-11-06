"""
Service for generating an OpenAPI spec
"""
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import typing

from dynapi.lib import get_datasets
from dynapi.domain.types import Type


@dataclass
class Parameter:
    name: str
    in_: str
    description: typing.Optional[str] = None
    required: bool = False



@dataclass
class MediaType:
    schema: dict

@dataclass
class Response:
    description: str
    content: typing.Dict[str, dict]

@dataclass
class Operation:
    operationId: str
    responses: typing.Dict[int, Response]
    parameters: typing.Optional[typing.List[Parameter]] = None


@dataclass
class PathItem:
    get: typing.Optional[Operation] = None
    put: typing.Optional[Operation] = None
    post: typing.Optional[Operation] = None
    delete: typing.Optional[Operation] = None
    parameters: typing.Optional[typing.List[Parameter]] = None


@dataclass
class Info:
    version: str = '0.0.1'
    title: str = "Some title"


@dataclass
class Components:
    schemas: typing.Dict[str, dict] = field(
        default_factory=dict
    )

@dataclass
class OpenAPI:
    info: Info
    openapi: str = '3.0.0'
    components: Components = field(
        default_factory=Components
    )
    paths: typing.Dict[str, PathItem] = field(
        default_factory=dict
    )

    def add_path_item(self, path: str, path_item: PathItem):
        self.paths[path] = path_item

    def dict(self):
        def _factory(inst):
            # remove trailing underscores
            return dict(
                (k.rstrip('_'), v) for k, v in inst if v
            )
        return asdict(
            self, dict_factory=_factory
        )


@dataclass
class OpenAPIContext:
    uri_path: str
    root_dir: str
    uri_version_prefix: str

    def compose_uri(self, catalog, collection, *optional_elements):
        return  "/".join([
            self.uri_path + self.uri_version_prefix,
            catalog, collection
        ] + list(optional_elements))

    
@dataclass
class OpenAPIService:
    context: OpenAPIContext

    def _get_types(self) -> typing.Iterator[Type]:
        return map(
            Type, get_datasets(self.context.root_dir)
        )
    
    def create_openapi_spec(self):
        def f(*segs):
            return "_".join(map(str.lower, segs))

        openapi = OpenAPI(
            info=Info(
                title="OpenAPI Amsterdam Schema",
                version="0.0.1",
            )
        )
        for catalog in self._get_types():
            for cls in catalog.classes:
                cls_name = cls["id"]
                primary_name = catalog.primary_names[cls_name]
                primary_name_description = cls["schema"]["properties"][primary_name][
                    "description"
                ]
                openapi.components.schemas[cls_name] = cls['schema']
                openapi.add_path_item(
                    self.context.compose_uri(
                        catalog.name, cls_name, f"{{{primary_name}}}"
                    ),
                    PathItem(
                        get=Operation(
                            operationId=f("get", cls_name),
                            responses={
                                200: Response(
                                    description=cls["id"],
                                    content={
                                        'application/json': {
                                            "schema": {
                                                "$ref": f"#/components/schemas/{cls_name}"
                                            }
                                        }
                                    }
                                )
                            }
                        ),
                        parameters=[
                            Parameter(
                                name=primary_name,
                                in_="path",
                                required=True,
                                description=primary_name_description,
                            )
                        ]
                    )
                )
        return openapi.dict()