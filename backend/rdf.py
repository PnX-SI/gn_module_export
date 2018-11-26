#!/usr/bin/env python

from datetime import datetime as dt
from shapely import wkt, geometry

from rdflib import (
    BNode,
    ConjunctiveGraph,
    URIRef,
    Literal,
    Namespace,
    RDF
)
from rdflib.namespace import FOAF, DC, XSD


DCMITYPE = Namespace('http://purl.org/dc/dcmitype/')
DWC = Namespace('http://rs.tdwg.org/dwc/terms/')
DSW = Namespace('http://purl.org/dsw/')


class OccurrenceStore:
    def __init__(self):
        self.graph = ConjunctiveGraph()
        self.graph.bind('dc', DC)
        self.graph.bind('foaf', FOAF)
        self.graph.bind('dwc', DWC)
        self.graph.bind('dsw', DSW)

    def save(self, store_uri, format='turtle'):
        self.graph.serialize(store_uri, format)

    def build_event(self, record):
        event = BNode()
        self.graph.add((event, RDF.type, DCMITYPE.Event))
        return event

    def build_human_observation(self, event, record):
        human_observation = BNode()
        self.graph.add((human_observation, RDF.type, DWC['HumanObservation']))
        self.graph.add((event, DSW['basisOfRecord'], human_observation))
        self.graph.add(
            (human_observation,
             DWC['eventDate'],
             Literal('/'.join([
                dt.isoformat(
                    dt.strptime(record['dateDebut'], '%Y-%d-%m %H:%M:%S')),
                dt.isoformat(
                    dt.strptime(record['dateFin'], '%Y-%d-%m %H:%M:%S'))]))))  # noqa: E131
        self.graph.add(
            (human_observation,
             DWC['eventTime'],
             Literal('/'.join([record['heureDebut'], record['heureFin']]))))
        self.graph.add(
            (human_observation, DWC['samplingProtocol'], Literal(record['obsMeth'])))  # noqa: E501
        self.graph.add(
            (human_observation, DWC['eventRemarks'], Literal(record['comment'])))  # noqa: E501
        self.graph.add(
            (human_observation, DWC['accessRights'], Literal(record['dSPublique'])))  # noqa: E501
        self.graph.add((human_observation, DWC['datasetName'], Literal(record['jddCode'])))  # noqa: E501
        self.graph.add(
            (human_observation, DWC['datasetId'], Literal(record['jddId'])))
        self.graph.add(
            (human_observation, DWC['ownerInstitutionCode'], Literal(record['orgGestDat'])))  # noqa: E501
        if 'obsId' in record.keys() and 'obsNomOrg' in record.keys():
            self.graph.add(
                (human_observation,
                 DWC['georeferencedBy'],
                 Literal('|'.join([record['obsId'], record['obsNomOrg']]))))
        elif 'obsId' in record.keys():
            self.graph.add(
                (human_observation, DWC['georeferencedBy'], Literal(record['obsId'])))  # noqa: E501
        elif 'obsNomOrg' in record.keys():
            self.graph.add(
                (human_observation, DWC['georeferencedBy'], Literal(record['obsNomOrg'])))  # noqa: E501
        return human_observation

    def build_location(self, human_observation, record):
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

        self.graph.add((human_observation, DSW['locatedAt'], location))
        return location

    def build_occurrence(self, event, record):
        occurrence = BNode()
        self.graph.add((occurrence, RDF.type, DWC['Occurrence']))
        # http://nomplateformeregionale/occtax/f0eevc75‐9c0b‐4ef8‐bz7z‐8zb9bz380g15
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
        self.graph.add((event, DSW['basisOfRecord'], occurrence))
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
            (identification, DWC['dateIdentified'], Literal(dt.isoformat(
                dt.strptime(record['dateDebut'], '%Y-%d-%m %H:%M:%S')))))
        if 'detId' in record.keys() and 'detNomOrg' in record.keys():
            self.graph.add(
                (organism,
                 DWC['identifiedBy'],
                 Literal('|'.join([record['detId'], record['detNomOrg']]))))
        elif 'detId' in record.keys():
            self.graph.add(
                (organism, DWC['identifiedBy'], Literal(record['detId'])))
        elif 'detNomOrg' in record.keys():
            self.graph.add(
                (organism, DWC['identifiedBy'], Literal(record['detNomOrg'])))

        self.graph.add((organism, DWC['hasIdentification'], identification))
        return identification

    def build_taxon(self, identification, record):
        taxon = BNode()
        self.graph.add((taxon, RDF.type, DWC['Taxon']))
        self.graph.add(
            (taxon, DWC['vernacularName'],
             Literal(record['nomCite'], lang='fr')))
        # self.graph.add((taxon, DWC['taxonID'], Literal(record['cdNom'])))
        self.graph.add(
            (taxon, DWC['taxonID'], URIRef(
                Literal(
                    'http://taxref.mnhn.fr/lod/taxon/{}/12.0'.format(
                        str(record['cdRef']))))))

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
    store = OccurrenceStore()
    event = store.build_event(record)
    human_observation = store.build_human_observation(event, record)
    location = store.build_location(human_observation, record)
    occurrence = store.build_occurrence(event, record)
    organism = store.build_organism(occurrence, record)
    identification = store.build_identification(organism, record)
    taxon = store.build_taxon(identification, record)
    store.save()
