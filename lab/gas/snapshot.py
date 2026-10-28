"""Saves what Rastro Lab's model reads, so the notebook (lab/notebooks/rastro-lab.ipynb) runs anywhere, Colab
included, without Postgres or Ontop: the same five inputs modelo.py reads (gas, the raw-table features A, the
Rastro features B, partners and operator changes) and the published run's predictions, with a manifest of
fingerprints. Runs on the machine with the oil and gas Ontop up, like modelo.py:

    python3 lab/gas/snapshot.py
"""
import hashlib
import json
from datetime import datetime, timezone

import modelo

OUT = modelo.RAIZ / "lab" / "notebooks" / "datos"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    run = modelo.sql_local("SELECT id, version, fecha FROM lab_gas.corrida WHERE vigente ORDER BY fecha DESC LIMIT 1")
    if run.empty or run.version[0] != modelo.version():
        raise SystemExit("The published run is not from this modelo.py: publish first (python3 lab/gas/modelo.py --publicar)")
    queries = {"gas": modelo.SQL_GAS, "a": modelo.SQL_A, "b": modelo.SPARQL_B, "socios": modelo.SPARQL_SOCIOS,
               "cambios": modelo.SPARQL_CAMBIOS}
    frames = {"gas": modelo.sql_local(modelo.SQL_GAS), "a": modelo.sql_local(modelo.SQL_A),
              "b": modelo.sparql_local(modelo.SPARQL_B), "socios": modelo.sparql_local(modelo.SPARQL_SOCIOS),
              "cambios": modelo.sparql_local(modelo.SPARQL_CAMBIOS),
              "predicciones": modelo.sql_local("SELECT idpozo, gas, minimo, maximo, de_prueba FROM lab_gas.prediccion "
                                               f"WHERE corrida = '{run.id[0]}' ORDER BY idpozo")}
    files = {}
    for name, frame in frames.items():   # B carries every value's rule and evidence: compressed, it stays small
        path = OUT / (f"{name}.csv.gz" if name == "b" else f"{name}.csv")
        frame.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0} if name == "b" else None)
        files[path.name] = {"rows": len(frame), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest = {"saved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "model_version": modelo.version(), "run": run.id[0], "files": files,
                "query_sha256": {k: hashlib.sha256(v.encode()).hexdigest() for k, v in queries.items()},
                "source": "Public data of the Secretaría de Energía (Argentina), read through Rastro; see README.md"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v["rows"] for k, v in files.items()}), "run", run.id[0])


if __name__ == "__main__":
    main()
