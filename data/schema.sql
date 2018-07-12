-- DROP TABLE gn_exports.cor_role_export;
CREATE TABLE gn_exports.cor_role_export
(
    id_cor_role_export SERIAL NOT NULL PRIMARY KEY,
    roles character(255) COLLATE pg_catalog."default",
)

-- DROP TABLE gn_exports.t_exports;
CREATE TABLE gn_exports.t_exports
(
    id SERIAL NOT NULL PRIMARY KEY,
    label text COLLATE pg_catalog."default" NOT NULL,
    selection text COLLATE pg_catalog."default" NOT NULL,
    start timestamp without time zone,
    "end" timestamp without time zone,
    status integer NOT NULL DEFAULT '-2'::integer,
    log text COLLATE pg_catalog."default",
    id_role integer NOT NULL,
    CONSTRAINT uniq_label UNIQUE (label),
    CONSTRAINT fk_admin FOREIGN KEY (id_role)
        REFERENCES utilisateurs.t_roles (id_role) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

-- DROP TABLE gn_exports.t_exports_logs;
CREATE TABLE gn_exports.t_exports_logs
(
    id SERIAL NOT NULL PRIMARY KEY,
    format integer NOT NULL,
    id_user integer NOT NULL,
    date timestamp without time zone NOT NULL,
    ip_addr character varying(45) COLLATE pg_catalog."default" NOT NULL,
    id_export integer,
    CONSTRAINT fk_export FOREIGN KEY (id_export)
        REFERENCES gn_exports.t_exports (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT fk_user FOREIGN KEY (id_user)
        REFERENCES utilisateurs.t_roles (id_role) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
