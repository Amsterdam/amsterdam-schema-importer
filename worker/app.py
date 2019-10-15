import logging
import os
import typing

from .interfaces import amsterdam_schema
from .generators.mapfile import (
    MapfileGenerator
)
from .interfaces.mapfile.serializers import (
    MappyfileSerializer
)


log = logging.getLogger(__name__)


def main(dataset_json):
    dataset = amsterdam_schema.AmsterdamSchema(dataset_json)
    return MapfileGenerator(
        map_dir="notused",
        serializer=MappyfileSerializer(),
        datasets=[]
    ).serialize(dataset)