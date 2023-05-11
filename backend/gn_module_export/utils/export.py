import csv
import json
import pathlib
from typing import Union

import fiona
from fiona.crs import from_epsg
from geonature.utils.env import db
from geonature.utils.errors import GeoNatureError
from utils_flask_sqla.schema import SmartRelationshipsMixin
from utils_flask_sqla_geo.schema import GeoAlchemyAutoSchema
from utils_flask_sqla_geo.utilsgeometry import FIONA_MAPPING


def get_model_from_generic_query(generic_query, pk_name: Union[str, None] = None):
    """
    renvoie un modèle SQLAlchemy à partir d'une Generic Query

    TODO (à déplacer dans les lib utils sqla)
    """
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
    """
    renvoie un marshmalow schema à partir d'un modèle
    ce schema hérite des classes GeoAlchemyAutoSchema et SmartRelationshipsMixin

    TODO (à déplacer dans les lib utils sqla)
    """
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
    columns: list = [],
    chunk_size: int = 1000,
    separator=";",
    primary_key_name: Union[str, None] = None,
    geometry_field_name=None,
):
    """Exporte une generic query au format csv

    la geométrie n'est pas présente par défaut
    elle peut être dans les données exportées si geometry_field_name est précisé

    Args:
        query (GenericQueryGeo): GenericQuery instanciée avec la vue, les filtre, le tri, etc..
        fp (_type_): pointer vers un fichier (un stream, etc..)
        columns (list, optioname): liste des colonnes à exporter. Defaults to [] (toutes les colonnes de la vue).
        chunk_size (int, optional): taille pour le traitement par lots. Defaults to 1000.
        separator (str, optional): sparateur pour le csv. Defaults to ";".
        primary_key_name (Union[str, None], optional): nom du champs de la clé primaire. Defaults to None.
        geometry_field_name (_type_, optional): nom du champ pour la colonne geométrique. Defaults to None.
    """
    # gestion de only
    only = columns

    # ajout du champs geométrique si demandé (sera exporté en WKT)
    if geometry_field_name:
        only.append(f"+{geometry_field_name}")

    # creation du schema marshmallow
    schema_class = get_schema_from_model(
        get_model_from_generic_query(query, pk_name=primary_key_name)
    )

    # instantiation du schema avec only
    schema = schema_class(only=only or None)

    # écriture du fichier cscv
    writer = csv.DictWriter(
        fp, columns, delimiter=separator, quoting=csv.QUOTE_ALL, extrasaction="ignore"
    )

    writer.writeheader()  # ligne d'entête

    # serialisation
    iterable_data = schema.dump(query.raw_query().yield_per(chunk_size), many=True)

    # écriture des lignes dans le fichier csv
    for line in iterable_data:
        writer.writerow(line)


def export_geojson(
    query,
    fp,
    columns: list = [],
    chunk_size: int = 1000,
    primary_key_name=None,
    geometry_field_name=None,
):
    """Exporte une generic query au format geojson

    le champs geomtrique peut être précisé
    ou choisi par défaut si la vue ne comporte qu'un seul champs geométrique

    Args:
        query (GenericQueryGeo): GenericQuery instanciée avec la vue, les filtre, le tri, etc..
        fp (_type_): pointer vers un fichier (un stream, etc..)
        columns (list, optioname): liste des colonnes à exporter. Defaults to [] (toutes les colonnes de la vue).
        chunk_size (int, optional): taille pour le traitement par lots. Defaults to 1000.
        primary_key_name (Union[str, None], optional): nom du champs de la clé primaire. Defaults to None.
        geometry_field_name (_type_, optional): nom du champ pour la colonne geométrique. Defaults to None.
    """

    # creation du schema marshmallow
    schema_class = get_schema_from_model(
        get_model_from_generic_query(query, pk_name=primary_key_name)
    )

    # instantiation du schema
    schema = schema_class(
        only=columns or None, as_geojson=True, feature_geometry=geometry_field_name
    )

    # serialisation
    feature_collection = schema.dump(query.raw_query().yield_per(chunk_size), many=True)

    # écriture du ficher geojson
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
    """Exporte une generic query au format json

    la geométrie n'est pas présente par défaut
    elle peut être dans les données exportées si geometry_field_name est précisé

    Args:
        query (GenericQueryGeo): GenericQuery instanciée avec la vue, les filtre, le tri, etc..
        fp (_type_): pointer vers un fichier (un stream, etc..)
        columns (list, optioname): liste des colonnes à exporter. Defaults to [] (toutes les colonnes de la vue).
        chunk_size (int, optional): taille pour le traitement par lots. Defaults to 1000.
        separator (str, optional): sparateur pour le csv. Defaults to ";".
        primary_key_name (Union[str, None], optional): nom du champs de la clé primaire. Defaults to None.
        geometry_field_name (_type_, optional): nom du champ pour la colonne geométrique. Defaults to None.
    """

    # gestion de only
    only = columns

    # ajout du champs geométrique si demandé (sera exporté en WKT)
    if geometry_field_name:
        only.append(f"+{geometry_field_name}")

    # creation du schema marshmallow
    schema_class = get_schema_from_model(
        get_model_from_generic_query(query, pk_name=primary_key_name)
    )

    # instantiation du schema avec only
    schema = schema_class(only=only or None)

    # serialisation
    iterable_data = schema.dump(query.raw_query().yield_per(chunk_size), many=True)

    # écriture du fichier json
    for chunk in json.JSONEncoder().iterencode(iterable_data):
        fp.write(chunk)


def export_geopackage(
    query,
    filename: str,
    geometry_field_name=None,
    columns: list = [],
    chunk_size: int = 1000,
    primary_key_name=None,
    srid=4326,
):
    schema_class = get_schema_from_model(
        get_model_from_generic_query(query, pk_name=primary_key_name)
    )

    schema = schema_class(
        only=columns or None, as_geojson=True, feature_geometry=geometry_field_name
    )

    feature_collection = schema.dump(query.raw_query().yield_per(chunk_size), many=True)
    # FIXME: filter tableDef columns with columns
    properties = {
        db_col.key: FIONA_MAPPING.get(db_col.type.__class__.__name__.lower(), "str")
        for db_col in query.view.tableDef.columns
        if not db_col.type.__class__.__name__ == "Geometry"
        and (not columns or db_col.key in columns)
    }
    gpkg_schema = {"geometry": "Unknown", "properties": properties}

    with fiona.open(filename, "w", "GPKG", schema=gpkg_schema, crs=from_epsg(srid)) as f:
        for feature in feature_collection["features"]:
            f.write(feature)
    # items = self.data.get("items")

    # for feature in items["features"]:
    #     geom, props = (feature.get(field) for field in ("geometry", "properties"))

    #     fionaService.create_feature(
    #         props, from_shape(asShape(geom), self.export.get("geometry_srid"))
    #     )

    # fionaService.save_files()
