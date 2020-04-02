from datetime import datetime as dt

from rdflib import (
    BNode,
    ConjunctiveGraph,
    URIRef,
    Literal,
    Namespace,
    RDF
)
from rdflib.namespace import FOAF, DC, XSD

from utils_flask_sqla.generic import GenericQuery

from geonature.utils.env import DB

DCMITYPE = Namespace('http://purl.org/dc/dcmitype/')
DWC = Namespace('http://rs.tdwg.org/dwc/terms/')
DSW = Namespace('http://purl.org/dsw/')
DCMTERMS = Namespace('http://purl.org/dc/terms')


class OccurrenceStore:
    def __init__(self):
        self.graph = ConjunctiveGraph()
        self.graph.bind('dc', DC)
        self.graph.bind('foaf', FOAF)
        self.graph.bind('dwc', DWC)
        self.graph.bind('dsw', DSW)
        self.graph.bind('dcterms', DCMTERMS)

    def save(self, store_uri, format_='turtle'):
        self.graph.serialize(store_uri, format_)

    def build_agent(self, who=None):
        agent = BNode()
        self.graph.add((agent, RDF.type, FOAF['Agent']))
        if who is not None:
            self.graph.add((agent, RDF.type, FOAF['Person']))
            self.graph.add((agent, FOAF['nick'], Literal(who)))
        return agent

    def build_recordlevel(self, record):
        recordlevel = BNode()
        self.graph.add((recordlevel, RDF.type, DCMTERMS.Event))
        self.graph.add((recordlevel, DCMTERMS['language'], Literal('fr')))
        self.graph.add((recordlevel, DWC['datasetID'], Literal(record['jddId'])))
        self.graph.add((recordlevel, DWC['datasetName'], Literal(record['jddCode'])))
        self.graph.add((recordlevel, DWC['ownerInstitutionCode'], Literal(record['ownerInstitutionCode'])))
        return recordlevel

    def build_event(self, recordlevel, record):
        event = BNode()
        self.graph.add((event, RDF.type, DWC['Event']))
        if 'permIdGrp' in record.keys():
            self.graph.add(
                (event, DWC['eventID'], Literal(record['permIdGrp'])))
        self.graph.add(
            (event,
             DWC['eventDate'],
             Literal('/'.join([
                dt.isoformat(
                    dt.strptime(record['dateDebut'], '%Y-%m-%d %H:%M:%S')),
                dt.isoformat(
                    dt.strptime(record['dateFin'], '%Y-%m-%d %H:%M:%S'))]))))
        self.graph.add(
            (event, DWC['samplingProtocol'], Literal(record['obsMeth'])))  # noqa: E501
        self.graph.add(
            (event, DWC['eventRemarks'], Literal(record['obsCtx'])))  # noqa: E501
        self.graph.add((recordlevel, DSW['basisOfRecord'], event))
        return event

    def build_location(self, event, record):
        location = BNode()
        self.graph.add((location, RDF.type, DCMTERMS['Location']))
        self.graph.add(
            (location, DWC['maximumElevationInMeters'], Literal(record['altMax'])))  # noqa: E501
        self.graph.add(
            (location, DWC['minimumElevationInMeters'], Literal(record['altMin'])))  # noqa: E501
        self.graph.add(
            (location, DWC['footprintWKT'], Literal(record['geom'])))
        self.graph.add((location, DWC['geodeticDatum'], Literal('EPSG:4326')))
        self.graph.add((
            location,
            DWC['coordinateUncertaintyInMeters'],
            Literal(record['difNivPrec'])
        ))
        self.graph.add(
            (location,
                DWC['decimalLatitude'],
                Literal(record['x_centroid'], datatype=XSD.float)))
        self.graph.add(
            (location,
                DWC['decimalLongitude'],
                Literal(record['y_centroid'], datatype=XSD.float)))
        self.graph.add((event, DSW['locatedAt'], location))
        return location

    def build_occurrence(self, event, record):
        # sameAs URIRef(
        #     Literal(
        # 'http://nomplateformeregionale/occtax/f0eevc75‐9c0b‐4ef8‐bz7z‐8zb9bz380g15'))
        occurrence = BNode()
        self.graph.add((occurrence, RDF.type, DWC['Occurrence']))
        self.graph.add(
            (occurrence, DWC['occurrenceID'], Literal(record['permId'])))
        self.graph.add(
            (occurrence, DWC['occurrenceStatus'], Literal(record['statObs'])))
        self.graph.add(
            (occurrence, DWC['occurrenceRemarks'], Literal(record['obsDescr'])))
        self.graph.add(
            (occurrence, DWC['organismQuantityType'], Literal(record['objDenbr'])))  # noqa: E501
        self.graph.add(
            (occurrence, DWC['occurrenceQuantity'], Literal(record['denbrMin'])))  # noqa: E501
        self.graph.add(
            (occurrence, DWC['establishmentMeans'], Literal(record['ocNat'])))
        self.graph.add(
           (occurrence, DWC['lifeStage'], Literal(record['ocStade'])))
        self.graph.add(
           (occurrence, DWC['occurrenceStatus'], Literal(record['statObs'])))

        if 'observer' in record.keys():
            observer = self.build_agent(record['observer'])
            self.graph.add(
            (occurrence, DWC['recordedBy'], observer))

        self.graph.add(
           (occurrence, DWC['occurrenceRemarks'], Literal(record['obsDescr'])))
        self.graph.add((occurrence, DSW['atEvent'], event))
        self.graph.add((event, DSW['eventOf'], occurrence))
        return occurrence

    def build_organism(self, occurrence, record):
        organism = BNode()
        self.graph.add((organism, RDF.type, DWC['Organism']))
        self.graph.add((occurrence, DSW['occurrenceOf'], organism))
        self.graph.add((organism, DSW['hasOccurrence'], occurrence))
        return organism

    def build_identification(self, organism, record):
        identification = BNode()
        self.graph.add((identification, RDF.type, DWC['Identification']))
        self.graph.add(
            (identification, DWC['identificationVerificationStatus'], Literal(record['preuveOui'])))  # noqa: E501
        self.graph.add(
            (identification, DWC['identificationRemarks'], Literal(record['preuvNoNum'])))  # noqa: E501

        if 'determiner' in record.keys():
            determiner = self.build_agent(record['determiner'])
            self.graph.add((identification, DWC['identifiedBy'], determiner))

        self.graph.add((identification, DSW['identifies'], organism))
        self.graph.add((organism, DSW['hasIdentification'], identification))
        return identification

    def build_taxon(self, identification, record):
        taxon = BNode()
        self.graph.add((taxon, RDF.type, DWC['Taxon']))
        self.graph.add((taxon, DWC['scientificName'],
                       Literal(record['nom_complet'])))
        self.graph.add(
            (taxon, DWC['vernacularName'],
             Literal(record['nomCite'], lang='fr')))
        self.graph.add((taxon, DWC['taxonID'], Literal(record['cdNom'])))
        # TODO : pour le moment version de taxref fixée à 12
        #  car la 13 n'est pas implémentée dans le lod
        #   a suivre
        self.graph.add(
            (taxon, DWC['taxonID'], URIRef(
                Literal(
                    'http://taxref.mnhn.fr/lod/taxon/{}/12.0'.format(
                        str(record['cdRef']))))))
        self.graph.add((taxon, DWC['nameAccordingTo'], Literal(record['vTAXREF'])))
        self.graph.add((identification, DSW['toTaxon'], taxon))
        return taxon


def populate_occurence_store(data):
    """
        Fonction qui génère un store
            à partir de données occurences

        TODO : mettre des try/catch
    """
    store = OccurrenceStore()
    for record in data:
        recordLevel = store.build_recordlevel(record)
        event = store.build_event(recordLevel, record)
        store.build_location(event, record)
        occurrence = store.build_occurrence(event, record)
        organism = store.build_organism(occurrence, record)
        identification = store.build_identification(organism, record)
        store.build_taxon(identification, record)

    return store


def generate_store_dws(limit=10, offset=0, filters=None):
    """
        Fonction qui :
            - récupère les données de la requete v_exports_synthese_sinp_rdf
            - les formattent en vu de leur export en RDF

        TODO : mettre des try/catch
    """
    filters = filters or {}
    # get data
    query = GenericQuery(
        DB, 'v_exports_synthese_sinp_rdf', 'gn_exports', filters=filters,
        limit=limit, offset=offset
    )
    data = query.return_query()

    # generate sematic data structure
    store = populate_occurence_store(data.get('items'))

    return store