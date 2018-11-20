#!/usr/bin/env python

import os
from shapely import wkt, geometry

from rdflib import (
    BNode,
    ConjunctiveGraph,
    # URIRef,
    Literal,
    Namespace,
    RDF
)
from rdflib.namespace import FOAF, DC, XSD


DCMITYPE = Namespace('http://purl.org/dc/dcmitype/')
DWC = Namespace('http://rs.tdwg.org/dwc/terms/')
DSW = Namespace('http://purl.org/dsw/')
STORE_FILE = os.path.expanduser(
    '~/geonature/backend/static/exports/etalab_export.ttl')
STORE_URI = ''.join(['file://', STORE_FILE])


class Store:
    def __init__(self):
        self.graph = ConjunctiveGraph()
        self.graph.bind('dc', DC)
        self.graph.bind('foaf', FOAF)
        self.graph.bind('dwc', DWC)
        self.graph.bind('dsw', DSW)

    def save(self):
        self.graph.serialize(STORE_URI, format='turtle')

    def build_event(self, record):
        event = BNode()
        self.graph.add((event, RDF.type, DCMITYPE.Event))
        self.graph.add(
            (event,
             DWC['eventDate'],
             Literal('/'.join([record['dateDebut'], record['dateFin']]))))
        self.graph.add(
            (event,
             DWC['eventTime'],
             Literal('/'.join([record['heureDebut'], record['heureFin']]))))
        self.graph.add(
            (event, DWC['samplingProtocol'], Literal(record['obsMeth'])))
        self.graph.add(
            (event, DWC['eventRemarks'], Literal(record['comment'])))
        self.graph.add(
            (event, DWC['accessRights'], Literal(record['dSPublique'])))
        self.graph.add((event, DWC['datasetName'], Literal(record['jddCode'])))
        self.graph.add((event, DWC['datasetId'], Literal(record['jddId'])))
        self.graph.add(
            (event, DWC['ownerInstitutionCode'], Literal(record['orgGestDat'])))  # noqa: E501
        if 'obsId' in record.keys() and 'obsNomOrg' in record.keys():
            self.graph.add(
                (event,
                 DWC['georeferencedBy'],
                 Literal('|'.join([record['obsId'], record['obsNomOrg']]))))
        elif 'obsId' in record.keys():
            self.graph.add(
                (event, DWC['georeferencedBy'], Literal(record['obsId'])))
        elif 'obsNomOrg' in record.keys():
            self.graph.add(
                (event, DWC['georeferencedBy'], Literal(record['obsNomOrg'])))
        humanObservation = BNode()
        self.graph.add((humanObservation, RDF.type, DWC['HumanObservation']))
        self.graph.add((event, DWC['basisOfRecord'], Literal(humanObservation)))  # noqa: E501
        return event

    def build_location(self, event, record):
        location = BNode()
        self.graph.add((location, RDF.type, DWC['Location']))
        self.graph.add(
            (location, DWC['maximumElevationInMeters'], Literal(record['altMax'])))  # noqa: E501
        self.graph.add(
            (location, DWC['minimumElevationInMeters'], Literal(record['altMin'])))  # noqa: E501
        self.graph.add((location, DWC['footprintWKT'], Literal(record['WKT'])))
        self.graph.add((location, DWC['geodeticDatum'], Literal('EPSG:4326')))
        self.graph.add(
            (location,
             DWC['coordinateIncertaintyInMeters'],
             Literal(record['diffusionNiveauPrecision'])))
        wkt_ = wkt.loads(record['WKT'])
        geometry_ = geometry.mapping(wkt_)
        # {'type': 'Point', 'coordinates': (6.5, 44.85)}
        self.graph.add(
            (location,
             DWC['decimalLatitude'],
             Literal(geometry_['coordinates'][0], datatype=XSD.float)))
        self.graph.add(
            (location,
             DWC['decimalLongitude'],
             Literal(geometry_['coordinates'][1], datatype=XSD.float)))

        self.graph.add((event, DSW['locatedAt'], location))
        return location

    def build_occurrence(self, event, record):
        occurrence = BNode()
        self.graph.add((occurrence, RDF.type, DWC['Occurrence']))
        self.graph.add(
            (occurrence, DWC['occurrenceID'], Literal(record['permId'])))
        self.graph.add(
            (occurrence, DWC['occurrenceStatus'], Literal(record['statObs'])))
        self.graph.add(
            (occurrence, DWC['occurrenceRemarks'], Literal(record['obsCtx'])))
        self.graph.add(
            (occurrence, DWC['occurrenceQuantityType'], Literal(record['objDenbr'])))  # noqa: E501
        self.graph.add(
            (occurrence, DWC['occurrenceQuantity'], Literal(record['denbrMin'])))  # noqa: E501
        self.graph.add(
            (occurrence, DWC['associatedReferences'], Literal(record['refBiblio'])))  # noqa: E501
        self.graph.add(
            (occurrence, DWC['establishmentMeans'], Literal(record['ocNat'])))
        self.graph.add(
            (occurrence, DWC['lifeStage'], Literal(record['ocStade'])))
        self.graph.add((event, DSW['ofEvent'], occurrence))
        return occurrence

    def build_organism(self, occurrence, record):
        organism = BNode()
        self.graph.add((organism, RDF.type, DWC['Organism']))
        self.graph.add((occurrence, DSW['occurrenceOf'], organism))
        return organism

    def build_identification(self, organism, record):
        identification = BNode()
        self.graph.add((identification, RDF.type, DWC['Identification']))
        self.graph.add(
            (identification, DWC['identificationStatus'], Literal(record['preuveOui'])))  # noqa: E501
        self.graph.add(
            (identification, DWC['identificationRemarks'], Literal(record['preuvNoNum'])))  # noqa: E501
        self.graph.add(
            (identification, DWC['dateIdentified'], Literal(record['datedet'])))  # noqa: E501
        if 'detId' in record.keys() and 'detNomOrg' in record.keys():
            self.graph.add(
                (event,
                 DWC['identifiedBy'],
                 Literal('|'.join([record['detId'], record['detNomOrg']]))))
        elif 'detId' in record.keys():
            self.graph.add(
                (event, DWC['identifiedBy'], Literal(record['detId'])))
        elif 'detNomOrg' in record.keys():
            self.graph.add(
                (event, DWC['identifiedBy'], Literal(record['detNomOrg'])))

        self.graph.add((organism, DWC['hasIdentification'], identification))
        return identification

    def build_taxon(self, identification, record):
        taxon = BNode()
        self.graph.add((taxon, RDF.type, DWC['Taxon']))
        self.graph.add((taxon, DWC['vernacularName'], Literal(record['nomCite'])))  # noqa: E501
        self.graph.add((taxon, DWC['acceptedNameUsageID'], Literal(record['cdNom'])))  # noqa: E501
        self.graph.add(
            (taxon,
             DWC['taxonID'],
             Literal('/'.join(['http://taxref.mnhn.fr/lod/name', str(record['cdRef'])]))))  # noqa: E501

        self.graph.add((identification, DSW['toTaxon'], taxon))
        return taxon


if __name__ == '__main__':
    record = {
        'permId': '311abde1-a45d-4daa-8475-b538637d37dd',
        'statObs': 'Pr',
        'nomCite': 'Ablette',
        'dateDebut': '2017-01-08 00:00:00',
        'dateFin': '2017-01-08 00:00:00',
        'heureDebut': '20:00:00',
        'heureFin': '23:00:00',
        'altMax': 1600,
        'altMin': 1600,
        'cdNom': 67111,
        'cdRef': 67111,
        'versionTAXREF': 'Taxref V11.0',
        'datedet': '2017-01-08 00:00:00',
        'comment': 'Troisieme test',
        'dSPublique': 'NSP',
        'jddMetadonneeDEEId': '4d331cae-65e4-4948-b0b2-a11bc5bb46c2',
        'statSource': '',
        'diffusionNiveauPrecision': 0,
        'idOrigine': '311abde1-a45d-4daa-8475-b538637d37dd',
        'jddCode': 'Contact aléatoire tous règnes confondus',
        'jddId': '4d331cae-65e4-4948-b0b2-a11bc5bb46c2',
        'refBiblio': '',
        'obsMeth': 23,
        'ocEtatBio': 1,
        'ocNat': 1,
        'ocSex': 2,
        'ocStade': 3,
        'ocBiogeo': 0,
        'ocStatBio': 1,
        'preuveOui': 0,
        'ocMethDet': 'Autre méthode de détermination',
        'preuvNum': '',
        'preuvNoNum': 'Poils de plumes',
        'obsCtx': 'Autre exemple test',
        'permIdGrp': 'b93a03d3-5e24-4d28-b68e-e0f75593f085',
        'methGrp': 'Relevé',
        'typGrp': 'OBS',
        'denbrMax': '1',
        'denbrMin': '1',
        'objDenbr': 'IND',
        'typDenbr': 'Co',
        'obsId': 'Administrateur test',
        'obsNomOrg': 'Autre',
        'detId': 'Donovan',
        'detNomOrg': 'NSP',
        'orgGestDat': 'NSP',
        'geom_4326': '',
        'WKT': 'POINT(6.5 44.85)',
        'natObjGeo': 'In'
    }
    store = Store()
    event = store.build_event(record)
    location = store.build_location(event, record)
    occurrence = store.build_occurrence(event, record)
    organism = store.build_organism(occurrence, record)
    identification = store.build_identification(organism, record)
    taxon = store.build_taxon(identification, record)
    store.save()
