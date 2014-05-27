-------------------------------------------------------------------

CREATE TABLE istat_regioni
(
  id_istat text  NOT NULL,
  toponimo text  NOT NULL,
  CONSTRAINT istat_regioni_pkey PRIMARY KEY (id_istat)
);

-------------------------------------------------------------------

CREATE TABLE istat_province
(
  id_istat text  NOT NULL,
  toponimo text  NOT NULL,
  idregione text  NOT NULL,
  sigla text  NOT NULL,
  CONSTRAINT istat_province_pkey PRIMARY KEY (id_istat),
  CONSTRAINT istat_province_idregione_fkey FOREIGN KEY (idregione)
      REFERENCES istat_regioni (id_istat) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT istat_province_sigla_key UNIQUE (sigla)
);

-------------------------------------------------------------------

CREATE TABLE istat_comuni
(
  id_istat text NOT NULL,
  toponimo text  NOT NULL,
  idprovincia text NOT NULL,
  CONSTRAINT istat_comuni_idprovincia_fkey FOREIGN KEY (idprovincia)
      REFERENCES istat_province (id_istat) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT istat_comuni_key UNIQUE (idprovincia, id_istat)
);

-------------------------------------------------------------------

CREATE TABLE codici_belfiore
(
  id text NOT NULL,
  id_regione text,
  id_provincia text,
  id_comune text,
  toponimo text ,
  CONSTRAINT codici_belfiore_pkey PRIMARY KEY (id)
);

-------------------------------------------------------------------

CREATE TABLE istat_loc_tipi
(
  id integer NOT NULL,
  tipo text NOT NULL,
  CONSTRAINT istat_loc_tipi_pkey PRIMARY KEY (id)
);
-------------------------------------------------------------------

CREATE TABLE istat_loc
(
  id integer NOT NULL,
  denom_loc text,
  centro_cl boolean,
  popres integer NOT NULL,
  maschi integer NOT NULL,
  famiglie integer NOT NULL,
  alloggi integer NOT NULL,
  edifici integer NOT NULL,
  cod_pro text NOT NULL,
  cod_com text NOT NULL,
  cod_loc text NOT NULL,
  loc2001 text,
  altitudine real,
  denom_pro text,
  denom_com text,
  sigla_prov text,
  tipo_loc integer NOT NULL,
  sez2001 text NOT NULL,
  CONSTRAINT istat_loc_pkey PRIMARY KEY (id),
  CONSTRAINT istat_loc_tipo_loc_fkey FOREIGN KEY (tipo_loc)
      REFERENCES istat_loc_tipi (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
SELECT AddGeometryColumn( 'istat_loc', 'the_geom', 32632, 'MULTIPOLYGON', 'XY');
SELECT CreateSpatialIndex('istat_loc', 'the_geom');
  
-------------------------------------------------------------------

CREATE TABLE fab_catasto
(
  gid integer NOT NULL,
  valenza text,
  esterconf text,
  codbo text,
  tipo text,
  dim real,
  ang real,
  posx real,
  posy real,
  pintx real,
  pinty real,
  sup real,
  belfiore text,
  zona_cens text,
  foglio text,
  allegato text,
  sviluppo text,
  fog_ann text,
  orig text,
  CONSTRAINT fab_catasto_pkey PRIMARY KEY (gid)
);
SELECT AddGeometryColumn( 'fab_catasto', 'the_geom', 32632, 'MULTIPOLYGON', 'XY');
SELECT CreateSpatialIndex('fab_catasto', 'the_geom');

------------------------------------------------------------------------

CREATE TABLE fab_10k
(
  gid integer NOT NULL,
  fid_1 integer,
  foglio text,
  codice text,
  record integer,
  topon text,
  area real,
  identif text,
  cod_com text,
  fid_2 integer,
  area_1 numeric,
  perimeter numeric,
  comune_ integer,
  comune_id integer,
  codistat91 text,
  provincia text,
  nomemai text,
  nomemin text,
  CONSTRAINT fab_10k_pkey PRIMARY KEY (gid)
);
SELECT AddGeometryColumn( 'fab_10k', 'the_geom', 32632, 'MULTIPOLYGON', 'XY');
SELECT CreateSpatialIndex('fab_10k', 'the_geom');

------------------------------------------------------------------------

CREATE TABLE fab_10k_mod
(
  "local_gid"   integer NOT NULL, -- chiave primaria nel db locale
  "gid"         integer NOT NULL, -- chiave primaria del record nel db remoto
  "identif"     text, -- aggregato identifier
  "fab_10k_gid" integer, -- source fab_10k record fk
  "mod_time"    date, -- client side modification datetime
  "team_id"     text, -- team identifier as API URL
  "upload_time" date, -- upload datetime
  CONSTRAINT fab_10k_mod_pkey PRIMARY KEY (local_gid)
);
SELECT AddGeometryColumn( 'fab_10k_mod', 'the_geom', 32632, 'MULTIPOLYGON', 'XY');
SELECT CreateSpatialIndex('fab_10k_mod', 'the_geom');

------------------------------------------------------------------------

CREATE TABLE "sopralluoghi" (
  "gid" integer NOT NULL PRIMARY KEY,
  "foglio" text,
  "codice" varchar(4),
  "record" float,
  "topon" varchar(50),
  "area" float,
  "identif" varchar(10),
  "id_hist" integer,
  "time_start" datetime,
  "time_end" datetime,
  "id_scheda" integer,
  "aggregato" text,
  "edificio" integer,
  "esito" varchar(1),
  "id_evento" integer,
  "controllo" boolean,
  "data" date
);
SELECT AddGeometryColumn( 'sopralluoghi', 'the_geom', 32632, 'MULTIPOLYGON', 'XY');
SELECT CreateSpatialIndex('sopralluoghi', 'the_geom');

CREATE INDEX "sopralluoghi_401bf584" ON "sopralluoghi" ("gid");

