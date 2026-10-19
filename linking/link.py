"""Enlaza ensayos de AACT con MeSH (condiciones) y con ChEMBL (fármacos).

Todo el enlace está en SQL legible: conditions.sql, drugs.sql, entities.sql y stop_reasons.sql (una
fila por fármaco, sponsor y target, que leen los mapeos). Este script los corre y
muestra cuánto enlazó.

Se corre con: docker compose run --rm linker
"""

import csv
import os
from pathlib import Path

import psycopg

HERE = Path(__file__).parent


def main():
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS linking")
        conn.execute("DROP TABLE IF EXISTS linking.regimen")
        conn.execute("CREATE TABLE linking.regimen (regimen text, drug text)")
        with conn.cursor().copy("COPY linking.regimen FROM STDIN") as copy:
            for row in csv.DictReader((HERE / "regimens.csv").open()):
                copy.write_row((row["regimen"], row["drug"]))

        conn.execute("DROP TABLE IF EXISTS linking.generic_word")
        conn.execute("CREATE TABLE linking.generic_word (word text PRIMARY KEY)")
        with conn.cursor().copy("COPY linking.generic_word FROM STDIN") as copy:
            for row in csv.DictReader((HERE / "generic_words.csv").open()):
                copy.write_row((row["word"],))

        conn.execute((HERE / "conditions.sql").read_text())
        conn.execute((HERE / "drugs.sql").read_text())
        conn.execute((HERE / "entities.sql").read_text())
        conn.execute((HERE / "stop_reasons.sql").read_text())

        print("Condiciones → MeSH")
        for r in conn.execute("""
            SELECT count(DISTINCT b.downcase_mesh_term),
                   count(DISTINCT b.downcase_mesh_term) FILTER (WHERE d.id IS NOT NULL),
                   (SELECT count(*) FROM aact.studies),
                   (SELECT count(DISTINCT nct_id) FROM linking.trial_condition)
            FROM aact.browse_conditions b
            LEFT JOIN mesh.descriptor d ON lower(d.label) = b.downcase_mesh_term
            WHERE b.mesh_type = 'mesh-list'"""):
            print(f"  términos enlazados: {r[1]} de {r[0]} ({100 * r[1] / r[0]:.1f} %)")
            print(f"  ensayos con condición: {r[3]} de {r[2]} ({100 * r[3] / r[2]:.1f} %)")

        print("Fármacos → ChEMBL")
        for r in conn.execute("""
            SELECT count(*), count(*) FILTER (WHERE EXISTS (
                SELECT 1 FROM linking.intervention_drug x WHERE x.id = i.id))
            FROM linking.intervention i"""):
            print(f"  intervenciones enlazadas: {r[1]} de {r[0]} ({100 * r[1] / r[0]:.1f} %)")
        for rule, n in conn.execute("SELECT rule, count(*) FROM linking.trial_drug GROUP BY 1 ORDER BY 2 DESC"):
            print(f"  enlaces por {rule}: {n}")
        n_trials, n_drugs = conn.execute(
            "SELECT count(DISTINCT nct_id), count(DISTINCT parent_chembl_id) FROM linking.trial_drug").fetchone()
        print(f"  {n_trials} ensayos con al menos un fármaco, {n_drugs} fármacos distintos")


if __name__ == "__main__":
    main()
