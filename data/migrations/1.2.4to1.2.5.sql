BEGIN;

-- Ajout de delete cascade sur les exports
ALTER TABLE gn_exports.cor_exports_roles
    DROP CONSTRAINT fk_cor_exports_roles_id_export,
    ADD CONSTRAINT fk_cor_exports_roles_id_export FOREIGN KEY (id_export) REFERENCES gn_exports.t_exports(id) ON DELETE CASCADE;

ALTER TABLE gn_exports.t_export_schedules
    DROP CONSTRAINT fk_t_export_schedules_id_export,
    ADD CONSTRAINT fk_t_export_schedules_id_export FOREIGN KEY (id_export) REFERENCES gn_exports.t_exports(id) ON DELETE CASCADE;


COMMIT;