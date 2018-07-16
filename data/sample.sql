SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

DROP VIEW gn_exports.mavue;
CREATE OR REPLACE VIEW gn_exports.mavue AS
  SELECT 'now'::text::date AS date;


COPY gn_exports.t_exports (id, label, selection, created, updated, id_role) FROM stdin;
1	Custom2	gn_exports.mavue	\N	\N	1
3	OccTax SINP	pr_occtax.export_occtax_dlb	\N	\N	1
\.

SELECT pg_catalog.setval('gn_exports.t_exports_id_seq', 5, true);
