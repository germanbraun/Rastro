-- Subconjunto de ChEMBL con los nombres de tablas y columnas del esquema original,
-- salvo que las claves son los ChEMBL ID (la API no expone molregno ni tid).
DROP SCHEMA IF EXISTS chembl CASCADE;
CREATE SCHEMA chembl;

CREATE TABLE chembl.molecule_dictionary (
    chembl_id           text PRIMARY KEY,
    pref_name           text,
    molecule_type       text,
    max_phase           numeric,
    first_approval      int,
    therapeutic_flag    boolean,
    oral                boolean,
    parenteral          boolean,
    topical             boolean,
    black_box_warning   int,
    withdrawn_flag      boolean,
    first_in_class      int,
    orphan              int,
    usan_stem           text,
    usan_stem_definition text,
    parent_chembl_id    text,
    active_chembl_id    text,   -- molécula activa: distinta de la propia si es una prodroga
    standard_inchi_key  text,
    canonical_smiles    text
);

CREATE TABLE chembl.molecule_synonyms (
    chembl_id   text NOT NULL REFERENCES chembl.molecule_dictionary,
    synonyms    text NOT NULL,
    syn_type    text NOT NULL
);

CREATE TABLE chembl.molecule_atc_classification (
    chembl_id   text NOT NULL REFERENCES chembl.molecule_dictionary,
    level5      text NOT NULL
);

CREATE TABLE chembl.drug_indication (
    drugind_id          int PRIMARY KEY,
    chembl_id           text NOT NULL REFERENCES chembl.molecule_dictionary,
    parent_chembl_id    text,
    max_phase_for_ind   numeric,
    mesh_id             text,
    mesh_heading        text,
    efo_id              text,
    efo_term            text
);

-- Referencias de cada indicación; las de tipo ClinicalTrials enlazan con aact.studies
CREATE TABLE chembl.indication_refs (
    drugind_id  int NOT NULL REFERENCES chembl.drug_indication,
    ref_type    text NOT NULL,
    ref_id      text NOT NULL,
    ref_url     text
);

CREATE TABLE chembl.target_dictionary (
    chembl_id           text PRIMARY KEY,
    pref_name           text,
    target_type         text,
    organism            text,
    species_group_flag  boolean
);

CREATE TABLE chembl.target_components (
    target_chembl_id        text NOT NULL REFERENCES chembl.target_dictionary,
    component_id            int NOT NULL,
    accession               text,
    component_type          text,
    component_description   text,
    relationship            text,
    gene_symbol             text
);

CREATE TABLE chembl.drug_mechanism (
    mec_id              int PRIMARY KEY,
    chembl_id           text NOT NULL REFERENCES chembl.molecule_dictionary,
    parent_chembl_id    text,
    mechanism_of_action text,
    action_type         text,
    target_chembl_id    text REFERENCES chembl.target_dictionary,
    direct_interaction  int,
    disease_efficacy    int,
    max_phase           numeric
);

-- UNII (FDA) por molécula, desde UniChem: la llave para enlazar con openFDA
CREATE TABLE chembl.unii_xref (
    chembl_id   text NOT NULL REFERENCES chembl.molecule_dictionary,
    unii        text NOT NULL
);

CREATE INDEX ON chembl.molecule_synonyms (chembl_id);
CREATE INDEX ON chembl.molecule_synonyms (lower(synonyms));
CREATE INDEX ON chembl.drug_indication (chembl_id);
CREATE INDEX ON chembl.drug_indication (mesh_id);
CREATE INDEX ON chembl.indication_refs (ref_type, ref_id);
CREATE INDEX ON chembl.drug_mechanism (chembl_id);
CREATE INDEX ON chembl.drug_mechanism (target_chembl_id);
CREATE INDEX ON chembl.target_components (accession);
CREATE INDEX ON chembl.unii_xref (unii);
