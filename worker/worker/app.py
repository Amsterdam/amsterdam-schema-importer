from .generators.mapfile import (
    MapfileGenerator
)
# XXX see generators/mapfile.py about this import
from .generators.schema import Dataset
from .interfaces.mapfile.serializers import (
    MappyfileSerializer
)


class CreateMapfileFromDataset:
    """ Creates a Mapfile from a dataset in JSON """

    _dataset_from_json = Dataset
    _generator = MapfileGenerator(
        serializer=MappyfileSerializer()
    )

    def __call__(self, dataset_json: str):
        dataset = self._dataset_from_json(dataset_json)
        return self._generator(dataset)
