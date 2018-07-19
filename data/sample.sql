--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.9
-- Dumped by pg_dump version 9.6.9

-- Started on 2018-07-19 10:30:02 CEST

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
-- TOC entry 4194 (class 0 OID 54851)
-- Dependencies: 374
-- Data for Name: t_exports; Type: TABLE DATA; Schema: gn_exports; Owner: geonatuser
--

INSERT INTO gn_exports.t_exports (id, label, schema_name, view_name, "desc", created, updated, deleted, id_role) VALUES (1, 'OccTax - Dépôt Légal de Biodiversité', 'pr_occtax', 'export_occtax_dlb', NULL, '2018-07-19 08:10:48.021199', NULL, NULL, 1);
INSERT INTO gn_exports.t_exports (id, label, schema_name, view_name, "desc", created, updated, deleted, id_role) VALUES (2, 'OccTax - SINP', 'pr_occtax', 'export_occtax_sinp', NULL, '2018-07-19 08:10:48.0212', '2018-07-19 08:10:48.021201', NULL, 1);


--
-- TOC entry 4200 (class 0 OID 0)
-- Dependencies: 373
-- Name: t_exports_id_seq; Type: SEQUENCE SET; Schema: gn_exports; Owner: geonatuser
--

SELECT pg_catalog.setval('gn_exports.t_exports_id_seq', 1, false);


-- Completed on 2018-07-19 10:30:02 CEST

--
-- PostgreSQL database dump complete
--

