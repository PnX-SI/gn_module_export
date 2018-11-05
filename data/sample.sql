SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

INSERT INTO gn_exports.t_exports (label, schema_name, view_name, "desc", geometry_field, geometry_srid, public) VALUES ('OccTax - DLB', 'pr_occtax', 'export_occtax_dlb', 'Dépôt Légal de Biodiversité', 'geom_4326', 4326, TRUE);
INSERT INTO gn_exports.t_exports (label, schema_name, view_name, "desc", geometry_field, geometry_srid, public) VALUES ('OccTax - SINP', 'pr_occtax', 'export_occtax_sinp', 'SINP compliant dataset', NULL, NULL, TRUE);

INSERT INTO gn_exports.cor_exports_roles (id_export, id_role) VALUES (1, 1);
INSERT INTO gn_exports.cor_exports_roles (id_export, id_role) VALUES (2, 1);
