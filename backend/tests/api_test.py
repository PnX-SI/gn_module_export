import os
from datetime import datetime
import pytest
from flask import url_for, current_app
from .bootstrap_test import (app, get_token)


assert app  # silence pyflake's unused import warning

REFERENCE_GRAPH = '''\
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dsw: <http://purl.org/dsw/> .
@prefix dwc: <http://rs.tdwg.org/dwc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a <http://purl.org/dc/dcmitype/Event> ;
dsw:basisOfRecord [ a dwc:Occurrence ;
    dsw:occurrenceOf [ a dwc:Organism ;
            dwc:hasIdentification [ a dwc:Identification ;
                    dsw:toTaxon [ a dwc:Taxon ;
                            dwc:taxonID <http://taxref.mnhn.fr/lod/taxon/351/12.0> ;
                            dwc:vernacularName "Grenouille rousse"@fr ] ;
                    dwc:dateIdentified "2017-01-01T00:00:00" ;
                    dwc:identificationRemarks "Poils de plumes" ;
                    dwc:identificationStatus "0" ] ;
            dwc:identifiedBy "Théo|NSP" ] ;
    dwc:associatedReferences "None" ;
    dwc:establishmentMeans "1" ;
    dwc:lifeStage "4" ;
    dwc:occurrenceID "d2e80898-0b25-49b5-a94a-9bb85073508e" ;
    dwc:occurrenceQuantity 1 ;
    dwc:occurrenceQuantityType "IND" ;
    dwc:occurrenceRemarks "Exemple test" ;
    dwc:occurrenceStatus "Pr" ],
[ a dwc:HumanObservation ;
    dsw:locatedAt [ a dwc:Location ;
            dwc:coordinateIncertaintyInMeters "0" ;
            dwc:decimalLatitude "6.5"^^xsd:float ;
            dwc:decimalLongitude "44.85"^^xsd:float ;
            dwc:footprintWKT "POINT(6.5 44.85)" ;
            dwc:geodeticDatum "EPSG:4326" ;
            dwc:maximumElevationInMeters 1565 ;
            dwc:minimumElevationInMeters 1500 ] ;
    dwc:accessRights "NSP" ;
    dwc:datasetId "4d331cae-65e4-4948-b0b2-a11bc5bb46c2" ;
    dwc:datasetName "Contact aléatoire tous règnes confondus" ;
    dwc:eventDate "2017-01-01T00:00:00/2017-01-01T00:00:00" ;
    dwc:eventRemarks "Autre test" ;
    dwc:eventTime "12:05:02/12:05:02" ;
    dwc:georeferencedBy "Administrateur test|Autre" ;
    dwc:ownerInstitutionCode "NSP" ;
    dwc:samplingProtocol "23" ] .

[] a <http://purl.org/dc/dcmitype/Event> ;
dsw:basisOfRecord [ a dwc:HumanObservation ;
    dsw:locatedAt [ a dwc:Location ;
            dwc:coordinateIncertaintyInMeters "0" ;
            dwc:decimalLatitude "6.5"^^xsd:float ;
            dwc:decimalLongitude "44.85"^^xsd:float ;
            dwc:footprintWKT "POINT(6.5 44.85)" ;
            dwc:geodeticDatum "EPSG:4326" ;
            dwc:maximumElevationInMeters 1565 ;
            dwc:minimumElevationInMeters 1500 ] ;
    dwc:accessRights "NSP" ;
    dwc:datasetId "4d331cae-65e4-4948-b0b2-a11bc5bb46c2" ;
    dwc:datasetName "Contact aléatoire tous règnes confondus" ;
    dwc:eventDate "2017-01-01T00:00:00/2017-01-01T00:00:00" ;
    dwc:eventRemarks "Test" ;
    dwc:eventTime "12:05:02/12:05:02" ;
    dwc:georeferencedBy "Administrateur test|Autre" ;
    dwc:ownerInstitutionCode "NSP" ;
    dwc:samplingProtocol "23" ],
[ a dwc:Occurrence ;
    dsw:occurrenceOf [ a dwc:Organism ;
            dwc:hasIdentification [ a dwc:Identification ;
                    dsw:toTaxon [ a dwc:Taxon ;
                            dwc:taxonID <http://taxref.mnhn.fr/lod/taxon/60612/12.0> ;
                            dwc:vernacularName "Lynx Boréal"@fr ] ;
                    dwc:dateIdentified "2017-01-01T00:00:00" ;
                    dwc:identificationRemarks "Poil" ;
                    dwc:identificationStatus "0" ] ;
            dwc:identifiedBy "Gil|NSP" ] ;
    dwc:associatedReferences "None" ;
    dwc:establishmentMeans "1" ;
    dwc:lifeStage "2" ;
    dwc:occurrenceID "c75053ca-8190-40c3-9bcd-5f9926211366" ;
    dwc:occurrenceQuantity 5 ;
    dwc:occurrenceQuantityType "IND" ;
    dwc:occurrenceRemarks "Exemple test" ;
    dwc:occurrenceStatus "Pr" ] .

[] a <http://purl.org/dc/dcmitype/Event> ;
dsw:basisOfRecord [ a dwc:Occurrence ;
    dsw:occurrenceOf [ a dwc:Organism ;
            dwc:hasIdentification [ a dwc:Identification ;
                    dsw:toTaxon [ a dwc:Taxon ;
                            dwc:taxonID <http://taxref.mnhn.fr/lod/taxon/67111/12.0> ;
                            dwc:vernacularName "Ablette"@fr ] ;
                    dwc:dateIdentified "2017-08-01T00:00:00" ;
                    dwc:identificationRemarks "Poils de plumes" ;
                    dwc:identificationStatus "0" ] ;
            dwc:identifiedBy "Donovan|NSP" ] ;
    dwc:associatedReferences "None" ;
    dwc:establishmentMeans "1" ;
    dwc:lifeStage "3" ;
    dwc:occurrenceID "311abde1-a45d-4daa-8475-b538637d37dd" ;
    dwc:occurrenceQuantity 1 ;
    dwc:occurrenceQuantityType "IND" ;
    dwc:occurrenceRemarks "Autre exemple test" ;
    dwc:occurrenceStatus "Pr" ],
[ a dwc:HumanObservation ;
    dsw:locatedAt [ a dwc:Location ;
            dwc:coordinateIncertaintyInMeters "0" ;
            dwc:decimalLatitude "6.5"^^xsd:float ;
            dwc:decimalLongitude "44.85"^^xsd:float ;
            dwc:footprintWKT "POINT(6.5 44.85)" ;
            dwc:geodeticDatum "EPSG:4326" ;
            dwc:maximumElevationInMeters 1600 ;
            dwc:minimumElevationInMeters 1600 ] ;
    dwc:accessRights "NSP" ;
    dwc:datasetId "4d331cae-65e4-4948-b0b2-a11bc5bb46c2" ;
    dwc:datasetName "Contact aléatoire tous règnes confondus" ;
    dwc:eventDate "2017-08-01T00:00:00/2017-08-01T00:00:00" ;
    dwc:eventRemarks "Troisieme test" ;
    dwc:eventTime "20:00:00/23:00:00" ;
    dwc:georeferencedBy "Administrateur test|Autre" ;
    dwc:ownerInstitutionCode "NSP" ;
    dwc:samplingProtocol "23" ] .
'''  # noqa: E501
admin_user = {
    'id_role': 1,
    'id_organisme': 1,
    'code_action': 'R',
    'code_filter': '3',
}
agent_user = {  # has only right on dataset 2
    'id_role': 2,
    'id_organisme': -1,
    'code_action': 'R',
    'code_filter': '2',
}
own_data_user = {  # can see only its data
    'id_role': 125,
    'id_organisme': -1,
    'code_action': 'R',
    'code_filter': '1',
}


@pytest.mark.usefixtures('client_class')
class TestApiModuleExports:
    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }

    def test_getExports(self):
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(url_for('exports.getExports'))
        assert response.status_code == 200

    def test_etalab(self):
        import rdflib
        from rdflib.compare  import isomorphic
        # from rdflib.tools.graphisomorphism import IsomorphicTestableGraph
        # from itertools import combinations

        conf = current_app.config.get('exports')
        try:
            os.unlink(conf.get('etalab_export'))
        except FileNotFoundError:
            pass
        response = self.client.get(url_for('exports.etalab_export'))
        assert response.status_code == 200

        # graph_name = {}
        # g1 = IsomorphicTestableGraph()
        # g1 = g1.parse(data=REFERENCE_GRAPH, format='turtle')
        # graph_name[g1] = 'REFERENCE_GRAPH'
        # g2 = IsomorphicTestableGraph()
        # g2 = g2.parse(data=REFERENCE_GRAPH, format='turtle')
        # graph_name[g2] = 'TESTED_GRAPH'
        # assert g1 == g2, "%s != %s" % (graph_name[g1], graph_name[g2])
        # >>> TypeError: unhashable type: 'IsomorphicTestableGraph'
        g1 = rdflib.Graph()
        g1 = g1.parse(data=REFERENCE_GRAPH, format='turtle')
        g2 = rdflib.Graph()
        g2 = g2.parse(data=response.data, format='turtle')
        # assert g2.isomorphic(g1)  # If no BNodes are involved
        # See rdflib.compare for a correct implementation of isomorphism checks
        assert isomorphic(g1, g2)

    def test_export_dlb_csv(self):
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        tick = datetime.now().replace(microsecond=0)
        response = self.client.get(
            url_for('exports.export', id_export=1, format='csv'))
        tock = datetime.now().replace(microsecond=0)
        assert response.status_code == 200

        content_disposition = set(
            response.headers['Content-Disposition'].split('; '))
        assert 'attachment' in content_disposition

        content_disposition = list(content_disposition)
        filenames = [
            item
            for item in content_disposition
            if item.startswith('filename=')]
        assert len(filenames) == 1

        filename = filenames[0].replace('filename=', '')
        assert filename.startswith('export_OccTax_-_DLB_')
        assert filename.endswith('.csv')
        ts = datetime.strptime(
                filename, 'export_OccTax_-_DLB_%Y_%m_%d_%Hh%Mm%S.csv'
            ).replace(microsecond=0)
        assert (tick <= ts <= tock)
        # assert somecontent in response.data

    def test_export_dlb_json(self):
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(
            url_for('exports.export', id_export=1, format='json'))
        assert response.status_code == 200

    def test_export_dlb_shp(self):
        # DLB has geom field
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(
            url_for('exports.export', id_export=1, format='shp'))
        assert response.status_code == 200

    def test_export_sinp_noshp(self):
        # SINP export has no geom field
        token = get_token(self.client)
        self.client.set_cookie('/', 'token', token)
        response = self.client.get(
            url_for('exports.export', id_export=2, format='shp'))
        assert response.status_code == 404
