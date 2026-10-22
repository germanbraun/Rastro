"""Link affiliation mentions to the Argentine ROR organizations they name, with the approved rules.

R0: the ROR identifier the publisher supplied, when the organization is Argentine (a shared key).
R1: a ROR name, label or alias of an Argentine organization (12 characters or more, normalized) appears as a whole
    phrase in the text, and the text also contains "Argentina" or one of the organization's ROR cities.
R2: an acronym used by only one Argentine organization appears as a separate word, with the same second evidence.
Anything else that looks like a candidate goes to afiliaciones.dudosa; reviewed decisions come from
linking/afiliaciones/correcciones.csv. Normalization is one function, used by every rule.

Run with: docker compose run --rm afiliaciones-linker
"""

import csv
import os
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import psycopg

HERE = Path(__file__).parent
CONTACT = re.compile(r"\S+@\S+|https?://\S+|www\.\S+")   # e-mails and web addresses are not evidence


def norm(text):
    """Lowercase, no accents, no punctuation, single spaces; contact data removed. The only normalization."""
    text = CONTACT.sub(" ", text or "")
    # Drop only the accents; any other symbol (including non-ASCII dashes such as — or ‐) becomes a space, so that
    # "Aires—CONICET" stays two words
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^0-9a-z]+", " ", text.lower()).strip()


def organizations(conn):
    """Argentine organizations with their names, acronyms and cities, from ROR."""
    rows = conn.execute("""
        SELECT n.id, n.value, n.types FROM ror.name n
        WHERE n.id IN (SELECT id FROM ror.location WHERE country_code = 'AR')""").fetchall()
    display = dict(conn.execute("""
        SELECT id, value FROM ror.name WHERE types LIKE '%ror_display%'
          AND id IN (SELECT id FROM ror.location WHERE country_code = 'AR')""").fetchall())
    cities = defaultdict(set)
    for org, city in conn.execute("SELECT id, city FROM ror.location WHERE country_code = 'AR' AND city IS NOT NULL"):
        cities[org].add(norm(city))
    names, acronyms = defaultdict(set), defaultdict(set)
    for org, value, types in rows:
        key, kinds = norm(value), set(types.split(","))
        if kinds & {"ror_display", "label", "alias"} and len(key) >= 12:
            names[key].add((org, value))
        if "acronym" in kinds and key:
            acronyms[key].add((org, value))
    return names, acronyms, cities, display


def second_evidence(text, org, cities):
    found = [c for c in sorted(cities[org]) if c and f" {c} " in text]
    if "argentin" in text:
        return "«Argentina»"
    return f"la ciudad «{found[0]}»" if found else None


def link(conn):
    names, acronyms, cities, display = organizations(conn)
    argentine = set(display)
    identified, doubtful = {}, {}
    mentions = conn.execute("SELECT doi, author_position, affiliation_position, name, ror_id FROM crossref.affiliation")
    for doi, ap, fp, raw, ror in mentions.fetchall():
        key, text = (doi, ap, fp), f" {norm(raw)} "
        if ror in argentine:
            identified[key + (ror,)] = ("R0: identificador ROR indicado por la editorial",
                                        f"La editorial indicó {ror} para «{raw}».")
        for name, orgs in names.items():
            if f" {name} " not in text:
                continue
            for org, value in orgs:
                second = second_evidence(text, org, cities)
                if second and key + (org,) not in identified:
                    identified[key + (org,)] = ("R1: nombre completo en ROR y una segunda evidencia",
                                                f"El texto «{raw}» contiene el nombre «{value}» de ROR y {second}.")
                elif not second:
                    doubtful[key + (org,)] = f"Nombre «{value}» sin una segunda evidencia (ni «Argentina» ni su ciudad)."
        words = set(text.split())
        for acronym, orgs in acronyms.items():
            if acronym not in words:
                continue
            for org, value in orgs:
                if key + (org,) in identified:
                    continue
                second = second_evidence(text, org, cities)
                if len(orgs) == 1 and second:
                    identified[key + (org,)] = ("R2: sigla única entre organizaciones argentinas y una segunda evidencia",
                                                f"El texto «{raw}» contiene la sigla «{value}», que en ROR usa solo "
                                                f"{display[org]}, y {second}.")
                else:
                    why = f"compartida por {len(orgs)} organizaciones argentinas" if len(orgs) > 1 else "sin una segunda evidencia"
                    doubtful[key + (org,)] = f"Sigla «{value}» {why}."
    for key in list(doubtful):
        if key in identified:
            del doubtful[key]
    return identified, doubtful


def corrections():
    path = HERE / "correcciones.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        return {(r["doi"], int(r["author_position"]), int(r["affiliation_position"]), r["organization"]):
                (r["decision"], r["reason"]) for r in csv.DictReader(f)}


def main():
    with psycopg.connect(host="postgres", port=5432, dbname=os.environ["PG_DB"], user=os.environ["PG_USER"],
                         password=os.environ["PG_PASSWORD"]) as conn:
        conn.execute((HERE / "links.sql").read_text())
        identified, doubtful = link(conn)
        reviewed = corrections()
        unknown = [k for k in reviewed if k not in doubtful]
        if unknown:
            raise SystemExit(f"Corrections for candidates the rules no longer produce: {unknown[:3]}")
        rows = [k + v + ("rule",) for k, v in identified.items()]
        rows += [k + ("Corrección revisada", f"{reason_d} Motivo: {reviewed[k][1]}", "correction-accepted")
                 for k, reason_d in doubtful.items() if reviewed.get(k, ("",))[0] == "accept"]
        with conn.cursor().copy("COPY afiliaciones.identificacion FROM STDIN") as cp:
            for r in rows:
                cp.write_row(r)
        with conn.cursor().copy("COPY afiliaciones.dudosa FROM STDIN") as cp:
            for k, reason in doubtful.items():
                decision, why = reviewed.get(k, (None, None))
                cp.write_row(k + (reason, decision, why))
        conn.execute("""
            INSERT INTO afiliaciones.sin_identificar
            SELECT a.doi, a.author_position, a.affiliation_position, a.name,
                   'Ninguna regla encontró una organización argentina de ROR en este texto.'
            FROM crossref.affiliation a
            WHERE a.name ~* 'argentin'
              AND NOT EXISTS (SELECT 1 FROM afiliaciones.identificacion i
                              WHERE (i.doi, i.author_position, i.affiliation_position)
                                    = (a.doi, a.author_position, a.affiliation_position))""")
        for label, sql in [("identificaciones por regla", "SELECT rule, count(*) FROM afiliaciones.identificacion GROUP BY 1 ORDER BY 1"),
                           ("dudosas", "SELECT coalesce(decision, 'sin revisar'), count(*) FROM afiliaciones.dudosa GROUP BY 1"),
                           ("sin identificar (mencionan Argentina)", "SELECT 'total', count(*) FROM afiliaciones.sin_identificar")]:
            print(label)
            for name, n in conn.execute(sql):
                print(f"  {name:<75}{n:>6}")


if __name__ == "__main__":
    main()
