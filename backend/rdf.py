from datetime import datetime as dt

from rdflib import BNode, ConjunctiveGraph, URIRef, Literal, Namespace, RDF
from rdflib.namespace import FOAF, DC, XSD

from utils_flask_sqla.generic import GenericQuery

from geonature.utils.env import DB

DCMITYPE = Namespace("http://purl.org/dc/dcmitype/")
DWC = Namespace("http://rs.tdwg.org/dwc/terms/")
DSW = Namespace("http://purl.org/dsw/")
DCMTERMS = Namespace("http://purl.org/dc/terms")


class OccurrenceStore:
    def __init__(self):
        self.graph = ConjunctiveGraph()
        self.graph.bind("dc", DC)
        self.graph.bind("foaf", FOAF)
        self.graph.bind("dwc", DWC)
        self.graph.bind("dsw", DSW)
        self.graph.bind("dcterms", DCMTERMS)

    def save(self, store_uri, format_="turtle"):
        self.graph.serialize(store_uri, format_)

    def _create_element_if_defined(self, property, type, value, as_litteral=True):
        # Test if value is defined and not in black list
        if not value:
            return
        if value in ("aucun", "Inconnu", "Ne Sait Pas", "None"):
            return

        if as_litteral:
            value = Literal(value)
        self.graph.add((property, type, value))

    def build_agent(self, who=None):
        agent = BNode()
        self.graph.add((agent, RDF.type, FOAF["Agent"]))
        if who is not None:
            self.graph.add((agent, RDF.type, FOAF["Person"]))
            self.graph.add((agent, FOAF["nick"], Literal(who)))
        return agent

    def build_recordlevel(self, record):
        recordlevel = URIRef(Literal(record["jddId"]))
        self.graph.add((recordlevel, RDF.type, DCMTERMS.Event))
        self.graph.add((recordlevel, DCMTERMS["language"], Literal("fr")))
        self.graph.add((recordlevel, DWC["datasetID"], Literal(record["jddId"])))
        self.graph.add((recordlevel, DWC["datasetName"], Literal(record["jddCode"])))
        self.graph.add(
            (
                recordlevel,
                DWC["ownerInstitutionCode"],
                Literal(record["ownerInstitutionCode"]),
            )
        )
        return recordlevel

    def build_event(self, recordlevel, record):
        if "permIdGrp" in record.keys():
            event = URIRef(Literal(record["permIdGrp"]))
        else:
            event = BNode()
        self.graph.add((event, RDF.type, DWC["Event"]))

        # cas période d'observation
        # Date séparée par un / cf https://dwc.tdwg.org/terms/#dwc:eventDate
        event_dates = [
            dt.isoformat(dt.strptime(record["dateDebut"], "%Y-%m-%d %H:%M:%S"))
        ]
        if not record["dateDebut"] == record["dateFin"]:
            event_dates.append(
                dt.isoformat(dt.strptime(record["dateFin"], "%Y-%m-%d %H:%M:%S"))
            )
        self.graph.add(
            (
                event,
                DWC["eventDate"],
                Literal("/".join(event_dates)),
            )
        )
        # self.graph.add(
        #     (event, DWC['samplingProtocol'], Literal(record['obsMeth'])))  # noqa: E501
        self._create_element_if_defined(event, DWC["eventRemarks"], record["obsCtx"])

        self.graph.add((recordlevel, DSW["basisOfRecord"], event))
        return event

    def build_location(self, event, record):
        # Si la localisation de l'événement est déjà défini
        if (event, DSW["locatedAt"], None) in self.graph:
            return

        location = BNode()
        self.graph.add((location, RDF.type, DCMTERMS["Location"]))

        self._create_element_if_defined(
            location, DWC["maximumElevationInMeters"], record["altMax"]
        )
        self._create_element_if_defined(
            location, DWC["minimumElevationInMeters"], record["altMin"]
        )
        self.graph.add((location, DWC["footprintWKT"], Literal(record["geom"])))
        self.graph.add((location, DWC["geodeticDatum"], Literal("EPSG:4326")))

        self._create_element_if_defined(
            location, DWC["coordinateUncertaintyInMeters"], record["difNivPrec"]
        )
        self.graph.add(
            (
                location,
                DWC["decimalLatitude"],
                Literal(record["x_centroid"], datatype=XSD.float),
            )
        )
        self.graph.add(
            (
                location,
                DWC["decimalLongitude"],
                Literal(record["y_centroid"], datatype=XSD.float),
            )
        )
        self.graph.add((event, DSW["locatedAt"], location))
        return location

    def build_occurrence(self, event, record):
        # sameAs URIRef(
        #     Literal(
        # 'http://nomplateformeregionale/occtax/f0eevc75‐9c0b‐4ef8‐bz7z‐8zb9bz380g15'))
        occurrence = BNode()
        self.graph.add((occurrence, RDF.type, DWC["Occurrence"]))
        self.graph.add((occurrence, DWC["occurrenceID"], Literal(record["permId"])))

        self._create_element_if_defined(
            occurrence, DWC["occurrenceStatus"], record["statObs"]
        )

        self._create_element_if_defined(
            occurrence, DWC["occurrenceRemarks"], record["obsDescr"]
        )

        self._create_element_if_defined(
            occurrence, DWC["organismQuantityType"], record["objDenbr"]
        )

        self._create_element_if_defined(
            occurrence, DWC["occurrenceQuantity"], record["denbrMin"]
        )

        self._create_element_if_defined(
            occurrence, DWC["establishmentMeans"], record["ocNat"]
        )

        self._create_element_if_defined(occurrence, DWC["lifeStage"], record["ocStade"])

        self._create_element_if_defined(
            occurrence, DWC["occurrenceStatus"], record["statObs"]
        )

        if "observer" in record.keys():
            observer = self.build_agent(record["observer"])
            self.graph.add((occurrence, DWC["recordedBy"], observer))

        self._create_element_if_defined(
            occurrence, DWC["occurrenceRemarks"], record["obsDescr"]
        )

        self.graph.add((occurrence, DSW["atEvent"], event))
        self.graph.add((event, DSW["eventOf"], occurrence))
        return occurrence

    def build_organism(self, occurrence, record):
        organism = BNode()
        self.graph.add((organism, RDF.type, DWC["Organism"]))
        self.graph.add((occurrence, DSW["occurrenceOf"], organism))
        self.graph.add((organism, DSW["hasOccurrence"], occurrence))
        return organism

    def build_identification(self, organism, record):
        identification = BNode()
        self.graph.add((identification, RDF.type, DWC["Identification"]))
        self._create_element_if_defined(
            identification, DWC["identificationVerificationStatus"], record["preuveOui"]
        )  # noqa: E501
        self._create_element_if_defined(
            identification, DWC["identificationRemarks"], record["preuvNoNum"]
        )  # noqa: E501

        if "determiner" in record.keys():
            determiner = self.build_agent(record["determiner"])
            self.graph.add((identification, DWC["identifiedBy"], determiner))

        self.graph.add((identification, DSW["identifies"], organism))
        self.graph.add((organism, DSW["hasIdentification"], identification))
        return identification

    def build_taxon(self, identification, record):
        # Il y a un soucis entre la définition du taxon au sens taxref
        #  c-a-d basé sur le cd_nom
        #  et le taxon au sens identification
        #       qui se base sur cd_nom avec potentiellement un nom cité parataxonomique

        # TODO : pour le moment version de taxref fixée à 12
        #  car la 13 n'est pas implémentée dans le lod
        #   a suivre
        taxon = URIRef(
            Literal(
                "http://taxref.mnhn.fr/lod/taxon/{}/13.0".format(str(record["cdRef"]))
            )
        )
        self.graph.add((taxon, RDF.type, DWC["Taxon"]))
        self.graph.add((taxon, DWC["scientificName"], Literal(record["nom_complet"])))
        # Désactivé car le nom cité ne correspond pas forcement au vernacularName
        #  et qui n'est pas unique pour un taxon
        # self.graph.add(
        #     (taxon, DWC["vernacularName"], Literal(record["nomCite"], lang="fr"))
        # )
        self.graph.add((taxon, DWC["taxonID"], Literal(record["cdNom"])))

        self.graph.add(
            (
                taxon,
                DWC["taxonID"],
                URIRef(
                    Literal(
                        "http://taxref.mnhn.fr/lod/taxon/{}/12.0".format(
                            str(record["cdRef"])
                        )
                    )
                ),
            )
        )
        self.graph.add((taxon, DWC["nameAccordingTo"], Literal(record["vTAXREF"])))
        self.graph.add((identification, DSW["toTaxon"], taxon))
        return taxon


def populate_occurence_store(data):
    """
    Fonction qui génère un store
        à partir de données occurrences

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
        - les formatte en vue de leur export en RDF

    TODO : mettre des try/catch
    """
    filters = filters or {}
    # get data
    query = GenericQuery(
        DB,
        "v_exports_synthese_sinp_rdf",
        "gn_exports",
        filters=filters,
        limit=limit,
        offset=offset,
    )
    data = query.return_query()

    # generate semantic data structure
    store = populate_occurence_store(data.get("items"))

    return store
