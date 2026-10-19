"""Arma las tablas del dominio de proveedores que leen los mapeos, y los enlaces.

entities.sql: una fila por proveedor, grupo y agencia, y proveedor → grupo con su evidencia.
links.sql: proveedor o grupo → LEI, → lista de control, y grupo → Wikidata, con su evidencia.
Todo está en SQL legible; este script los corre y muestra cuánto enlazó.

Se corre con: docker compose run --rm proveedores-linker
"""

import os
from pathlib import Path

import psycopg

HERE = Path(__file__).parent


def main():
    conninfo = (f"host=postgres port=5432 dbname={os.environ['PG_DB']} "
                f"user={os.environ['PG_USER']} password={os.environ['PG_PASSWORD']}")
    with psycopg.connect(conninfo) as conn:
        conn.execute((HERE / "entities.sql").read_text())
        for table in ("supplier", "group_company", "supplier_group", "agency", "sector", "sector_ancestor"):
            n = conn.execute(f"SELECT count(*) FROM proveedores.{table}").fetchone()[0]
            print(f"  proveedores.{table:<16}{n:>8} filas")

        if not conn.execute("SELECT to_regclass('gleif.lei_record')").fetchone()[0]:
            print("GLEIF todavía no está cargado: no se arman los enlaces.")
            return
        conn.execute((HERE / "links.sql").read_text())
        print("Enlaces con LEI (GLEIF)")
        for kind, searched, linked in conn.execute("""
                SELECT n.kind, count(*) FILTER (WHERE EXISTS (SELECT 1 FROM gleif.name_query q WHERE q.name = n.name)),
                       count(l.lei)
                FROM proveedores.company_name n LEFT JOIN proveedores.lei_link l USING (kind, uei)
                GROUP BY 1 ORDER BY 1"""):
            print(f"  {kind:<9} buscados en GLEIF: {searched:>5}, enlazados: {linked:>5}")
        for rule, n in conn.execute("SELECT rule, count(*) FROM proveedores.lei_link GROUP BY 1 ORDER BY 2 DESC"):
            print(f"    por {rule}: {n}")
        n = conn.execute("SELECT count(*) FROM proveedores.watchlist_link").fetchone()[0]
        print(f"Coincidencias con listas de control: {n}")
        n, listed = conn.execute("SELECT count(*), count(*) FILTER (WHERE listed) FROM proveedores.group_wikidata").fetchone()
        print(f"Grupos con Wikidata: {n}, cotizan en bolsa: {listed}")


if __name__ == "__main__":
    main()
