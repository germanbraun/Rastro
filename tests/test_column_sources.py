"""answer.column_sources decides the source the app shows next to each column of an answer, read from the oil and
gas mapping: a column from one term takes that term's sources; a computed one (SUM) takes all the query's sources."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "layer"))
import answer  # noqa: E402

PREFIX = "PREFIX energia: <https://w3id.org/rastro/energia#>\n"


def test_one_source_query():
    used, columns = answer.column_sources(PREFIX + """SELECT ?pozo ?petroleo WHERE {
      ?w a energia:Well ; energia:wellId ?pozo . ?p a energia:WellProduction ; energia:well ?w ; energia:oil ?petroleo .
    }""", "energia")
    assert used == ["capitulo4"] and columns == {"pozo": ["capitulo4"], "petroleo": ["capitulo4"]}


def test_a_term_keeps_its_source_and_a_sum_takes_all():
    used, columns = answer.column_sources(PREFIX + """SELECT ?pct (SUM(?oil * ?pct / 100) AS ?parte) WHERE {
      ?p a energia:WellProduction ; energia:inConcession ?c ; energia:oil ?oil .
      ?s a energia:Stake ; energia:inConcession ?c ; energia:percent ?pct .
    } GROUP BY ?pct""", "energia")
    assert used == ["capitulo4", "rastro", "sig_energia"]
    assert columns["pct"] == ["rastro", "sig_energia"]       # the stake: the map's text, split by Rastro
    assert columns["parte"] == used                          # computed from both
