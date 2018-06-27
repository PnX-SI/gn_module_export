--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.9
-- Dumped by pg_dump version 10.4 (Debian 10.4-2.pgdg90+1)

-- Started on 2018-06-27 10:15:10 CEST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 4194 (class 0 OID 134003)
-- Dependencies: 387
-- Data for Name: t_exports; Type: TABLE DATA; Schema: gn_exports; Owner: geonatuser
--

COPY gn_exports.t_exports (id, label, selection) FROM stdin;
1	SINP	SELECT  export_occtax_dlb."nomCite",\n          export_occtax_dlb."dateDebut",\n          export_occtax_dlb."dateFin",\n          export_occtax_dlb."heureDebut",\n          export_occtax_dlb."heureFin",\n          export_occtax_dlb."altMax",\n          export_occtax_dlb."altMin",\n          export_occtax_dlb."cdNom",\n          export_occtax_dlb."cdRef"\n  FROM pr_occtax.export_occtax_dlb
3	N°1	select CURRENT_DATE as date
4	N°2	select localtime as time
2	DarwinCore	SELECT  export_occtax_dlb."permId" AS "OccurrenceID",\n          concat(export_occtax_dlb."statObs", ' ', export_occtax_dlb."statSource") AS "OccurrenceStatus",\n          export_occtax_dlb."nomCite" AS "ScientificName",\n          concat(export_occtax_dlb."dateDebut", ' ',export_occtax_dlb."heureDebut", ', ', export_occtax_dlb."dateFin",' ', export_occtax_dlb."heureFin") AS "eventDate",\n          export_occtax_dlb."altMax" AS "maximumElevationInMeters",\n          export_occtax_dlb."altMin" AS "minimumElevationInMeters",\n          export_occtax_dlb."cdNom" AS "taxonID",\n          export_occtax_dlb."dateDet" AS "dateIdentified",\n          export_occtax_dlb.comment AS "occurrenceRemarks",\n          export_occtax_dlb."idOrigine" AS "CatalogNumber",\n          export_occtax_dlb."jddId" AS "CollectionId",\n          export_occtax_dlb."refBiblio" AS "associatedReferences",\n          export_occtax_dlb."ocMethDet" AS "basisOfRecord",\n          export_occtax_dlb."denbrMin" AS "Individual Count",\n          export_occtax_dlb."detId" AS "identifiedBy",\n          export_occtax_dlb."orgGestDat" AS "InstitutionCode",\n          export_occtax_dlb."WKT" AS "footprintWKT"\n  FROM pr_occtax.export_occtax_dlb
\.


--
-- TOC entry 4201 (class 0 OID 0)
-- Dependencies: 386
-- Name: t_exports_id_seq; Type: SEQUENCE SET; Schema: gn_exports; Owner: geonatuser
--

SELECT pg_catalog.setval('gn_exports.t_exports_id_seq', 1, true);


-- Completed on 2018-06-27 10:15:11 CEST

--
-- PostgreSQL database dump complete
--

