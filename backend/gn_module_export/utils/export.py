import csv
import json
import pathlib
from typing import Union

from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from utils_flask_sqla_geo.schema import GeoAlchemyAutoSchema
from utils_flask_sqla.schema import SmartRelationshipsMixin


class SerializableGenerator(list):
    def __init__(self, gen):
        self.gen = gen
        try:
            self.first_item = next(gen)
            self.empty = False
        except StopIteration:
            self.empty = True

    def __iter__(self):
        if not self.empty:
            yield self.first_item
            yield from self.gen

    def __bool__(self):
        return not self.empty

    __repr__ = object.__repr__


def get_model_from_generic_query(generic_query, pk_name: Union[str, None] = None):
    view = generic_query.view
    if pk_name is None:
        pk_name = str(view.tableDef.columns.keys()[0])

    if not hasattr(view.tableDef.c, pk_name):
        raise GeoNatureError(f"{pk_name} cannot be found in table")

    dict_model = {
        "__table__": view.tableDef,
        "__mapper_args__": {"primary_key": getattr(view.tableDef.c, pk_name)},
    }

    Model = type("Model", (db.Model,), dict_model)

    return Model


def get_schema_from_model(model):
    Meta = type(
        "Meta",
        (),
        {
            "model": model,
            "load_instance": True,
        },
    )
    dict_schema = {
        "Meta": Meta,
    }

    return type(
        "Schema",
        (
            GeoAlchemyAutoSchema,
            SmartRelationshipsMixin,
        ),
        dict_schema,
    )


def export_csv(
    query,
    fp,
    columns: list,
    chunk_size: int = 1000,
    separator=";",
    primary_key_name: Union[str, None] = None,
    geometry_field_name=None,
):
    schema_class = get_schema_from_model(
        get_model_from_generic_query(query, pk_name=primary_key_name)
    )
    schema = schema_class(only=columns)

    only = columns
    if geometry_field_name:
        only.append(f"+{geometry_field_name}")

    schema = schema_class(only=only or None)

    writer = csv.DictWriter(
        fp, columns, delimiter=separator, quoting=csv.QUOTE_ALL, extrasaction="ignore"
    )
    writer.writeheader()  # ligne d'entête
    for line in query.raw_query().yield_per(chunk_size):
        # TODO: Use Marshmallow?
        writer.writerow(schema.dump(line))


def export_geojson(
    query,
    fp,
    columns: list,
    chunk_size: int = 1000,
    primary_key_name=None,
    geometry_field_name=None,
):
    schema_class = get_schema_from_model(
        get_model_from_generic_query(query, pk_name=primary_key_name)
    )
    schema = schema_class(only=columns, as_geojson=True, feature_geometry=geometry_field_name)

    feature_collection = schema.dump(query.raw_query().yield_per(chunk_size), many=True)

    for chunk in json.JSONEncoder().iterencode(feature_collection):
        fp.write(chunk)


def export_json(
    query,
    fp,
    columns: list = [],
    chunk_size: int = 1000,
    primary_key_name=None,
    geometry_field_name=None,
):
    schema_class = get_schema_from_model(
        get_model_from_generic_query(query, pk_name=primary_key_name)
    )

    only = columns
    if geometry_field_name:
        only.append(f"+{geometry_field_name}")

    schema = schema_class(only=only or None)

    feature_collection = schema.dump(query.raw_query().yield_per(chunk_size), many=True)

    for chunk in json.JSONEncoder().iterencode(feature_collection):
        fp.write(chunk)
