from collections import ChainMap
from dataclasses import dataclass
import typing

from ..interfaces.amsterdam_schema import AmsterdamSchema
from ..interfaces.mapfile import types, serializers


@dataclass
class Generator:
    datasets: typing.List[object]
    map_dir: str

    def load_datasets(self):
        raise NotImplementedError

    def serialize(self, dataset) -> str:
        raise NotImplementedError

    def write(self, dataset, serialized):
        fp = f"{self.map_dir}/{dataset.name}.map"
        with open(fp, "w") as fh:
            fh.write(serialized)

    def __call__(self):
        for dataset in self.datasets:
            serialized = self.serialize(dataset)
            self.write(dataset, serialized)


@dataclass
class MapfileGenerator(Generator):
    serializer: serializers.MappyfileSerializer

    def generate_feature_class(self,
                               feature_dict,
                               base_styles=None) -> types.FeatureClass:
        feature_class = types.FeatureClass(
            name=feature_dict['name'],
            expression=feature_dict.get('expression')
        )
        styles = feature_dict.get('styles', base_styles)

        for index, style in enumerate(styles):
            base_style: dict = {}
            try:
                base_style = base_styles[index]
            except IndexError:
                pass
            feature_class.add_style(
                ChainMap(style, base_style)
            )
        return feature_class

    def generate_layer(self, dataset, name, layer_dict) -> types.Layer:
        styles = layer_dict.get('base_styles', [])
        features = layer_dict.get('features', [])
        srid_str = dataset.get('crs', 'EPSG:28992')
        srid = int(srid_str.split(':')[-1])

        layer = types.Layer(
            name=name,
            type=types.LayerType.polygon,
            classes=[],
            projection=layer_dict.get('projection', None),
            include=["connection_various_small_datasets.inc"],
            data=[types.Data.for_postgres(
                layer_dict['field'], layer_dict['dataset_class'],
                srid=srid, UNIQUE="id"
            )],
            metadata=types.Metadata(layer_dict.get('metadata', {}))
        )
        for feature_dict in features:
            layer.classes.append(
                self.generate_feature_class(
                    feature_dict, styles
                )
            )
        return layer

    def serialize(self, dataset: AmsterdamSchema) -> str:
        mapservice_data = dataset['services']['mapservice']
        mapfile = types.Mapfile(
            name=dataset['id'],
            layers=[],
            include=['header.inc'],
            projection=mapservice_data.get('projection', None)
        )
        try:
            mapfile.web = types.Web(
                types.Metadata(mapservice_data['web']['metadata'])
            )
        except KeyError:
            pass

        for name, layer_dict in mapservice_data.get('layers', {}).items():
            mapfile.layers.append(
                self.generate_layer(
                    dataset, name, layer_dict
                )
            )

        return self.serializer(mapfile)


@dataclass
class LegacyMapfileGenerator(Generator):
    serializer: serializers.JinjaSerializer

    def serialize(self, dataset) -> str:
        ds_dict = dataset.__dict__

        # get layers
        ds_dict["layers"] = map(
            lambda x: x.__dict__, dataset.maplayer_set.all()
        )
        ds_dict["id_field"] = dataset.pk_field

        template_file = 'default.map.template'
        if dataset.map_template:
            template_file = dataset.map_template

        return self.serializer(template_file, context={
            'ds': ds_dict
        })
