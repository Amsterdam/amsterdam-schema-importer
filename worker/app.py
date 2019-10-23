import logging
import os
import sys
import typing

from .interfaces import amsterdam_schema, json_
from .generators.mapfile import (
    MapfileGenerator
)
from .interfaces.mapfile.serializers import (
    MappyfileSerializer
)


log = logging.getLogger(__name__)


def main(dataset_json):
    dataset = amsterdam_schema.Dataset(dataset_json)
    return MapfileGenerator(
        serializer=MappyfileSerializer()
    ).serialize(dataset)


if __name__ == '__main__':
    fp = sys.argv[1]
    with open(fp, "r") as fh:
        json =json_.load(fh)
        print(main(
            json
        ))