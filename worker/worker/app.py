from dataservices import amsterdam_schema
from .interfaces import json_
from .generators.mapfile import (
    MapfileGenerator
)
from .interfaces.mapfile.serializers import (
    MappyfileSerializer
)


class CreateMapfileFromDataset:
    """ Creates a Mapfile from a dataset in JSON """

    _dataset_from_json = amsterdam_schema.Dataset
    _generator = MapfileGenerator(
        serializer=MappyfileSerializer()
    )

    def __call__(self, dataset_json: str):
        dataset = self._dataset_from_json(dataset_json)
        return self._generator(dataset)
