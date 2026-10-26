"""Link affiliation mentions to the Argentine ROR organizations they name, with the approved rules.

R0: the ROR identifier the publisher supplied, when the organization is Argentine (a shared key).
R1: a ROR name, label or alias of an Argentine organization (12 characters or more, normalized) appears as a whole
    phrase in the text, and the text also contains "Argentina" or one of the organization's ROR cities.
R2: an acronym used by only one Argentine organization appears as a separate word, with the same second evidence.
    A generic acronym (the initials of several Argentine organizations' names, such as CCT for every Centro Científico
    Tecnológico) is not enough: it names the one of that family whose own ROR acronym is in the same segment
    («CCT-CONICET La Plata» holds «CONICET-LA PLATA»); «CONICET, Rosario» without «CCT» is an address.
Mention text keeps its segments: a name never matches across a comma, semicolon, parenthesis, bracket or slash, and
a name followed by «de», «del» or «of» and something that is not a place is the start of a longer name, so it is only
a candidate.
Anything else that looks like a candidate goes to afiliaciones.dudosa; reviewed decisions come from
linking/afiliaciones/correcciones.csv. Normalization is one function, used by every rule.
For cq3, segments that name an institution and that no Argentine ROR name covers go to afiliaciones.posible_hueco,
in every mention with an Argentine context (it mentions Argentina or has an identification), as candidates.

Run with: docker compose run --rm afiliaciones-linker
"""

import csv
import html
import os
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import psycopg

HERE = Path(__file__).parent
CONTACT = re.compile(r"\S+@\S+|https?://\S+|www\.\S+")   # e-mails and web addresses are not evidence
FOOTNOTE = re.compile(r"^([A-Z])(?=[A-ZÁÉÍÓÚ][a-záéíóúñ]{3,})")   # «AUniversidad…»: a footnote letter glued to the name
SEGMENT = re.compile(r"[,;()\[\]/]")   # boundaries a name cannot cross in a mention
CONTINUES = {"de", "del", "of"}   # after a matched name, the start of a longer name
CONNECTORS = {"de", "del", "la", "las", "los", "el", "y", "e", "of", "the", "and", "for", "en", "para"}
# «… de Buenos Aires», «… de la Provincia de …»: a place after the name does not make it a longer name
PLACES = {"provincia", "buenos aires", "catamarca", "chaco", "chubut", "cordoba", "corrientes", "entre rios", "formosa",
          "jujuy", "la pampa", "la rioja", "mendoza", "misiones", "neuquen", "rio negro", "salta", "san juan", "san luis",
          "santa cruz", "santa fe", "santiago del estero", "tierra del fuego", "tucuman", "argentina"}
INSTITUTION = re.compile(r"^(instituto|institute|laboratorio|laboratory|centro|center|centre|hospital|fundacion|"
                         r"foundation|unidad|unit|observatorio|observatory|museo|museum|estacion|station)\b")


def norm(text, segments=False):
    """Lowercase, no accents, no punctuation, single spaces; contact data and a glued footnote letter removed. The
    only normalization. With segments=True (mention texts), segment boundaries stay as « | »."""
    text = FOOTNOTE.sub("", CONTACT.sub(" ", html.unescape(text or "")).strip())   # publishers leave HTML entities
    if segments:
        text = SEGMENT.sub(" | ", text)
    # Drop only the accents; any other symbol (including non-ASCII dashes such as — or ‐) becomes a space, so that
    # "Aires—CONICET" stays two words
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^0-9a-z|]+" if segments else r"[^0-9a-z]+", " ", text.lower()).strip()


def initials(name, size):
    words = [w for w in norm(name).split() if w not in CONNECTORS]
    return "".join(w[0] for w in words[:size])


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
    # A generic acronym: the initials of the names of more than one Argentine organization («CCT» for every Centro
    # Científico Tecnológico)
    generic = {}
    for key in acronyms:
        family = {org for org, value in display.items() if initials(value, len(key)) == key} if " " not in key else set()
        if len(key) <= 6 and len(family) > 1:
            generic[key] = family
    return names, acronyms, cities, display, generic


def second_evidence(text, org, cities, city_only=False):
    found = [c for c in sorted(cities[org]) if c and f" {c} " in text]
    if "argentin" in text and not city_only:
        return "«Argentina»"
    return f"la ciudad «{found[0]}»" if found else None


def link(conn):
    names, acronyms, cities, display, generic = organizations(conn)
    argentine = set(display)
    identified, doubtful = {}, {}
    mentions = conn.execute("SELECT doi, author_position, affiliation_position, name, ror_id FROM crossref.affiliation")
    for doi, ap, fp, raw, ror in mentions.fetchall():
        key, text = (doi, ap, fp), f" {norm(raw, segments=True)} "
        if ror in argentine:
            identified[key + (ror,)] = ("R0: identificador ROR indicado por la editorial",
                                        f"La editorial indicó {ror} para «{raw}».")
        for name, orgs in names.items():
            if f" {name} " not in text:
                continue
            after = text.split(f" {name} ", 1)[1].split("|", 1)[0].split()
            rest = " ".join(w for w in after[1:] if w not in {"la", "el", "las", "los"})
            longer = bool(after) and after[0] in CONTINUES and not any(
                rest.startswith(place) for place in PLACES | {c for o, _ in orgs for c in cities[o]})
            for org, value in orgs:
                second = second_evidence(text, org, cities)
                if longer:
                    if key + (org,) not in identified:
                        doubtful[key + (org,)] = f"Nombre «{value}» seguido de «{after[0]}»: puede ser el comienzo de un nombre más largo."
                elif second and key + (org,) not in identified:
                    identified[key + (org,)] = ("R1: nombre completo en ROR y una segunda evidencia",
                                                f"El texto «{raw}» contiene el nombre «{value}» de ROR y {second}.")
                elif not second:
                    doubtful[key + (org,)] = f"Nombre «{value}» sin una segunda evidencia (ni «Argentina» ni su ciudad)."
        words = set(text.split())
        for acronym, family in generic.items():   # «CCT» plus the organization's own acronym in one segment
            for segment in text.split("|"):
                if acronym not in segment.split():
                    continue
                for org in family:
                    form = next((a for a, orgs in acronyms.items() if " " in a and f" {a} " in f" {segment} "
                                 and {o for o, _ in orgs} == {org}), None)
                    if form and key + (org,) not in identified:
                        identified[key + (org,)] = (
                            "R2: sigla genérica junto a la sigla propia de la organización",
                            f"El texto «{raw}» contiene la sigla «{acronym.upper()}», común a varias organizaciones "
                            f"argentinas, y en el mismo tramo «{form.upper()}», la sigla que ROR da a {display[org]}.")
        for acronym, orgs in acronyms.items():
            if acronym not in words:
                continue
            for org, value in orgs:
                if key + (org,) in identified:
                    continue
                second = second_evidence(text, org, cities, city_only=acronym in generic)
                if acronym in generic and key + (org,) in identified:
                    continue
                if len(orgs) == 1 and second:
                    identified[key + (org,)] = ("R2: sigla única entre organizaciones argentinas y una segunda evidencia",
                                                f"El texto «{raw}» contiene la sigla «{value}», que en ROR usa solo "
                                                f"{display[org]}, y {second}.")
                else:
                    why = (f"compartida por {len(orgs)} organizaciones argentinas" if len(orgs) > 1
                           else "genérica (las iniciales de varias organizaciones argentinas) y sin su ciudad"
                           if acronym in generic else "sin una segunda evidencia")
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
                (r["decision"], r["reason"] + (f" Fuente: {r['source']}" if r.get("source") else ""),
                 r["human_confirmation"])
                for r in csv.DictReader(f)}


def possible_gaps(conn, names):
    """Segments that name an institution and that no Argentine ROR name covers, in mentions with an Argentine context."""
    known = list(names)
    rows = conn.execute("""
        SELECT a.doi, a.author_position, a.affiliation_position, a.name FROM crossref.affiliation a
        WHERE a.name ~* 'argentin' OR EXISTS (SELECT 1 FROM afiliaciones.identificacion i
              WHERE (i.doi, i.author_position, i.affiliation_position) = (a.doi, a.author_position, a.affiliation_position))
    """).fetchall()
    gaps = {}
    for doi, ap, fp, raw in rows:
        for part in re.split(r"[,;()\[\]/]|\s[-–—‐]\s", CONTACT.sub(" ", html.unescape(raw or ""))):
            segment, key = part.strip(" .*"), norm(part)
            if not INSTITUTION.match(key) or len(key) < 15:
                continue
            if any(name in key or key in name for name in known):
                continue
            gaps[(doi, ap, fp, segment)] = ("La búsqueda heurística no encontró un nombre de organización argentina de ROR "
                                              "que cubra este tramo.")
    return gaps


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
                decision, why, confirmation = reviewed.get(k, (None, None, None))
                cp.write_row(k + (reason, decision, why, confirmation))
        gaps = possible_gaps(conn, organizations(conn)[0])   # before the COPY: one command at a time
        with conn.cursor().copy("COPY afiliaciones.posible_hueco FROM STDIN") as cp:
            for k, reason in gaps.items():
                cp.write_row(k + (reason,))
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
                           ("sin identificar (mencionan Argentina)", "SELECT 'total', count(*) FROM afiliaciones.sin_identificar"),
                           ("posibles huecos (cq3, candidatos)", "SELECT 'segmentos', count(*) FROM afiliaciones.posible_hueco")]:
            print(label)
            for name, n in conn.execute(sql):
                print(f"  {name:<75}{n:>6}")


if __name__ == "__main__":
    main()
