--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.9
-- Dumped by pg_dump version 9.6.9

-- Started on 2018-07-19 08:32:42 CEST

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
-- TOC entry 4195 (class 0 OID 54712)
-- Dependencies: 374
-- Data for Name: t_exports; Type: TABLE DATA; Schema: gn_exports; Owner: geonatuser
--

COPY gn_exports.t_exports (id, id_role, label, schema_name, view_name, "desc", created, updated, deleted) FROM stdin;
1	1	OccTax - Dépôt Légal de Biodiversité	pr_occtax	export_occtax_dlb	\N	2018-07-19 08:10:48.021199	\N	\N
2	1	OccTax - SINP	pr_occtax	export_occtax_sinp	\N	2018-07-19 08:10:48.0212	2018-07-19 08:10:48.021201	\N
\.


--
-- TOC entry 4202 (class 0 OID 0)
-- Dependencies: 373
-- Name: t_exports_id_seq; Type: SEQUENCE SET; Schema: gn_exports; Owner: geonatuser
--

SELECT pg_catalog.setval('gn_exports.t_exports_id_seq', 1, false);


-- Completed on 2018-07-19 08:32:42 CEST

--
-- PostgreSQL database dump complete
--

