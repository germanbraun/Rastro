"""Carga en el esquema local `chembl` el subconjunto de ChEMBL de oncología.

Oncología = familias de moléculas (padre y sales) con alguna indicación bajo
"Neoplasms" (MeSH C04), el mismo criterio que el recorte de AACT. Se cargan sinónimos, ATC,
indicaciones (todas, no solo las oncológicas), mecanismos, targets y el UNII de
UniChem para enlazar con openFDA.

Se corre con: docker compose run --rm chembl-loader
"""

import gzip
import os
from pathlib import Path

import psycopg
import requests
from requests.adapters import HTTPAdapter, Retry

CHEMBL = "https://www.ebi.ac.uk/chembl/api/data"
MESH_SPARQL = "https://id.nlm.nih.gov/mesh/sparql"
UNICHEM_CHEMBL_TO_UNII = (
    "https://ftp.ebi.ac.uk/pub/databases/chembl/UniChem/data/"
    "wholeSourceMapping/src_id1/src1src14.txt.gz"
)
NEOPLASMS_TREE = "C04"
BATCH = 50  # IDs por request en los filtros __in

http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=2,
                                                     status_forcelist=[429, 500, 502, 503, 504])))


def get_json(url, **params):
    r = http.get(url, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def paginate(resource, **params):
    """Recorre todas las páginas de un recurso de la API de ChEMBL."""
    data = get_json(f"{CHEMBL}/{resource}.json", limit=1000, **params)
    key = next(k for k in data if k != "page_meta")
    while True:
        yield from data[key]
        nxt = data["page_meta"]["next"]
        if not nxt:
            return
        data = get_json(f"https://www.ebi.ac.uk{nxt}")


def fetch_by_ids(resource, id_field, ids):
    ids = sorted(ids)
    for i in range(0, len(ids), BATCH):
        yield from paginate(resource, **{f"{id_field}__in": ",".join(ids[i:i + BATCH])})


def neoplasm_descriptors():
    query = f"""
        PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?d FROM <http://id.nlm.nih.gov/mesh> WHERE {{
            ?d a meshv:TopicalDescriptor ; meshv:treeNumber ?t .
            ?t rdfs:label ?l . FILTER(STRSTARTS(?l, "{NEOPLASMS_TREE}"))
        }}"""
    r = http.get(MESH_SPARQL, params={"query": query, "format": "CSV"}, timeout=120)
    r.raise_for_status()
    return {line.rsplit("/", 1)[-1] for line in r.text.splitlines()[1:] if line}


def num(v):
    return float(v) if v not in (None, "") else None


def main():
    version = get_json(f"{CHEMBL}/status.json")["chembl_db_version"]
    print(f"Origen: {version} (API)")

    mesh_c04 = neoplasm_descriptors()
    print(f"Descriptores MeSH bajo Neoplasms: {len(mesh_c04)}")

    all_indications = list(paginate("drug_indication"))
    # Se trabaja por familia (molécula padre y sus sales): ChEMBL registra indicaciones
    # y mecanismos sobre cualquiera de las dos, y la resolución de entidades usa la padre.
    oncology = [i for i in all_indications if i["mesh_id"] in mesh_c04]
    parent_ids = {i["parent_molecule_chembl_id"] for i in oncology}
    print(f"Familias con indicación oncológica: {len(parent_ids)}")

    indications = [i for i in all_indications if i["parent_molecule_chembl_id"] in parent_ids]
    mechanisms = [m for m in paginate("mechanism") if m["parent_molecule_chembl_id"] in parent_ids]
    molecule_ids = (parent_ids
                    | {i["molecule_chembl_id"] for i in indications}
                    | {m["molecule_chembl_id"] for m in mechanisms})
    molecules = list(fetch_by_ids("molecule", "molecule_chembl_id", molecule_ids))
    target_ids = {m["target_chembl_id"] for m in mechanisms if m["target_chembl_id"]}
    targets = list(fetch_by_ids("target", "target_chembl_id", target_ids))

    raw = http.get(UNICHEM_CHEMBL_TO_UNII, timeout=300)
    raw.raise_for_status()
    unii = [line.split("\t") for line in gzip.decompress(raw.content).decode().splitlines()[1:]]
    unii = [(c, u) for c, u in unii if c in molecule_ids]

    rows = {
        "molecule_dictionary": [
            (m["molecule_chembl_id"], m["pref_name"], m["molecule_type"], num(m["max_phase"]),
             m["first_approval"], m["therapeutic_flag"], m["oral"], m["parenteral"], m["topical"],
             m["black_box_warning"], m["withdrawn_flag"], m["first_in_class"], m["orphan"],
             m["usan_stem"], m["usan_stem_definition"],
             (m["molecule_hierarchy"] or {}).get("parent_chembl_id"),
             (m["molecule_hierarchy"] or {}).get("active_chembl_id"),
             (m["molecule_structures"] or {}).get("standard_inchi_key"),
             (m["molecule_structures"] or {}).get("canonical_smiles"))
            for m in molecules],
        "molecule_synonyms": sorted({
            (m["molecule_chembl_id"], s["molecule_synonym"], s["syn_type"])
            for m in molecules for s in m["molecule_synonyms"]}),
        "molecule_atc_classification": [
            (m["molecule_chembl_id"], atc) for m in molecules for atc in m["atc_classifications"]],
        "drug_indication": [
            (i["drugind_id"], i["molecule_chembl_id"], i["parent_molecule_chembl_id"],
             num(i["max_phase_for_ind"]), i["mesh_id"], i["mesh_heading"], i["efo_id"], i["efo_term"])
            for i in indications],
        # Una referencia ClinicalTrials puede listar varios NCT separados por coma
        "indication_refs": [
            (i["drugind_id"], r["ref_type"], ref_id.strip(), r["ref_url"])
            for i in indications for r in i["indication_refs"]
            for ref_id in (r["ref_id"].split(",") if r["ref_type"] == "ClinicalTrials" else [r["ref_id"]])],
        "target_dictionary": [
            (t["target_chembl_id"], t["pref_name"], t["target_type"], t["organism"], t["species_group_flag"])
            for t in targets],
        "target_components": [
            (t["target_chembl_id"], c["component_id"], c["accession"], c["component_type"],
             c["component_description"], c["relationship"],
             next((s["component_synonym"] for s in c["target_component_synonyms"]
                   if s["syn_type"] == "GENE_SYMBOL"), None))
            for t in targets for c in t["target_components"]],
        "drug_mechanism": [
            (m["mec_id"], m["molecule_chembl_id"], m["parent_molecule_chembl_id"],
             m["mechanism_of_action"], m["action_type"], m["target_chembl_id"],
             m["direct_interaction"], m["disease_efficacy"], num(m["max_phase"]))
            for m in mechanisms],
        "unii_xref": unii,
    }

    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        conn.execute(Path(__file__).with_name("schema.sql").read_text())
        for table, data in rows.items():  # orden de inserción respeta las claves foráneas
            with conn.cursor().copy(f"COPY chembl.{table} FROM STDIN") as copy:
                for row in data:
                    copy.write_row(row)
            conn.execute(
                "INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count) "
                "VALUES ('chembl', %s, %s, %s)", (version, f"chembl.{table}", len(data)))
            print(f"  {table:<28}{len(data):>10} filas")
        conn.execute("ANALYZE")
        print("Listo.")
        for r in conn.execute("SELECT * FROM rastro_meta.source_counts WHERE source_id = 'chembl'"):
            print(r)


if __name__ == "__main__":
    main()
