"""Arma las tablas del dominio de proveedores que leen los mapeos, y los enlaces.

entities.sql: una fila por proveedor, grupo y agencia, y proveedor → grupo con su evidencia.
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


if __name__ == "__main__":
    main()
