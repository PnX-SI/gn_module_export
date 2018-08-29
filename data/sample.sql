SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

INSERT INTO gn_exports.t_exports (id, label, schema_name, view_name, "desc", geometry_field, geometry_srid) VALUES (1, 'OccTax - Dépôt Légal de Biodiversité', 'pr_occtax', 'export_occtax_dlb', NULL, 'geom_4326', 4326);
INSERT INTO gn_exports.t_exports (id, label, schema_name, view_name, "desc", geometry_field, geometry_srid) VALUES (2, 'OccTax - SINP', 'pr_occtax', 'export_occtax_sinp', NULL, NULL, NULL);

SELECT pg_catalog.setval('gn_exports.t_exports_id_seq', 1, false);
