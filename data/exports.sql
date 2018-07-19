CREATE SCHEMA IF NOT EXISTS gn_exports;

DROP TABLE IF EXISTS gn_exports.t_exports;
CREATE TABLE gn_exports.t_exports
(
    id SERIAL NOT NULL PRIMARY KEY,
    label text COLLATE pg_catalog."default" NOT NULL,
    schema_name text COLLATE pg_catalog."default" NOT NULL,
    view_name text COLLATE pg_catalog."default" NOT NULL,
    "desc" text COLLATE pg_catalog."default",
    created timestamp without time zone,
    updated timestamp without time zone,
    deleted timestamp without time zone,
    id_creator integer NOT NULL,
    CONSTRAINT uniq_label UNIQUE (label),
    CONSTRAINT fk_creator FOREIGN KEY (id_creator)
        REFERENCES utilisateurs.t_roles (id_role) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

DROP TABLE IF EXISTS gn_exports.t_exports_logs;
CREATE TABLE gn_exports.t_exports_logs
(
    id SERIAL NOT NULL PRIMARY KEY,
    format character varying(4) COLLATE pg_catalog."default" NOT NULL,
    id_user integer NOT NULL,
    date timestamp without time zone NOT NULL,
    ip_addr_port character varying(51) COLLATE pg_catalog."default" NOT NULL,
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
