SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET idle_in_transaction_session_timeout = 0;
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SELECT pg_catalog.set_config('search_path', '', false);
SET row_security = off;

INSERT INTO gn_exports.t_exports (id, label, schema_name, view_name, "desc", geometry_field, geometry_srid, public) VALUES (1, 'OccTax - DLB', 'pr_occtax', 'export_occtax_dlb', 'Dépôt Légal de Biodiversité', 'geom_4326', 4326, true);
INSERT INTO gn_exports.t_exports (id, label, schema_name, view_name, "desc", geometry_field, geometry_srid, public) VALUES (2, 'OccTax - SINP', 'pr_occtax', 'export_occtax_sinp', 'SINP compliant dataset', NULL, NULL, true);
INSERT INTO gn_exports.t_exports (id, label, schema_name, view_name, "desc", geometry_field, geometry_srid, public) VALUES (3, 'TRoles', 'utilisateurs', 't_roles', 'users', NULL, NULL, false);
SELECT pg_catalog.setval('gn_exports.t_exports_id_seq', 3, true);

INSERT INTO gn_exports.cor_exports_roles (id_export, id_role) VALUES (1, 1);
INSERT INTO gn_exports.cor_exports_roles (id_export, id_role) VALUES (2, 1);
INSERT INTO gn_exports.cor_exports_roles (id_export, id_role) VALUES (3, 1);
