"""Check that the Layer story preserves the calculation and source identity."""
import sys
from pathlib import Path

import pytest
import rdflib
import yaml
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'app'), str(ROOT / 'layer')]
E = 'https://w3id.org/rastro/energia#'
PREFIX = f'PREFIX energia: <{E}>\nPREFIX prov: <http://www.w3.org/ns/prov#>\n'


@pytest.fixture
def story_graph():
    graph = rdflib.Graph().parse(data='''
@prefix energia: <https://w3id.org/rastro/energia#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix : <https://example.org/> .
:c energia:name "LOMA CAMPANA" .
:company energia:name "CHEVRON" .
:other energia:name "OTRA" .
:source energia:name "Fuente original" .
:w energia:wellId "1" .
:p1 a energia:WellProduction; energia:inConcession :c; energia:oil 1000000; energia:gas 20;
 energia:well :w; energia:fromSource :source .
:p2 a energia:WellProduction; energia:inConcession :c; energia:oil 2000000; energia:gas 40;
 energia:well :w; energia:fromSource :source .
:s a energia:Stake; energia:inConcession :c; energia:partner :company; energia:percent 50;
 energia:sourceText "Nombre original: 50 %"; energia:rule "texto de socios";
 prov:wasDerivedFrom :source; prov:wasGeneratedBy :activity .
:s2 a energia:Stake; energia:inConcession :c; energia:partner :other; energia:percent 50;
 energia:sourceText "Otra empresa: 50 %"; energia:rule "texto de socios";
 prov:wasDerivedFrom :source; prov:wasGeneratedBy :activity .
:n a energia:CompanyName; energia:company :company; energia:nameInSource "Nombre original";
 energia:rule "corrección revisada"; energia:sourceText "pendiente de confirmación humana";
 prov:wasDerivedFrom :source .
''', format='turtle')
    return graph


def test_explanation_reconciles_without_counting_other_partners(story_graph):
    why = yaml.safe_load((ROOT / 'app/dominios/energia.yaml').read_text())['preguntas'][0]['porque']
    rows = list(story_graph.query(PREFIX + why['query'].replace('{valor}', 'CHEVRON')))
    assert len(rows) == 1
    assert float(rows[0].produccion) == 3000000
    assert float(rows[0].parte) == 1500000
    assert str(rows[0].empresa) == 'https://example.org/company'
    assert str(rows[0].texto) == 'Nombre original: 50 %'
    assert str(rows[0].origen) == 'https://example.org/source'


@pytest.mark.parametrize('tech', [False, True])
def test_story_renders_and_selection_updates(story_graph, tech):
    story_graph.parse(data=PREFIX + '''
PREFIX : <https://example.org/>
:c2 energia:name "OTRA CONCESIÓN" .
:p3 a energia:WellProduction; energia:inConcession :c2; energia:oil 2000000; energia:gas 40 .
:s3 a energia:Stake; energia:inConcession :c2; energia:partner :company; energia:percent 25;
 energia:sourceText "Nombre original: 25 %"; energia:rule "texto de socios";
 prov:wasDerivedFrom :source; prov:wasGeneratedBy :activity .
''', format='turtle')
    # Use the actual queries and RDF evaluation; stub only the network transport.
    script = f'''
import sys
sys.path[:0] = [{str(ROOT / 'app')!r}, {str(ROOT / 'layer')!r}]
from pathlib import Path
from unittest.mock import patch
import rdflib, yaml
import dominio
from layer_story import show_story
graph = rdflib.Graph().parse(data={story_graph.serialize(format='turtle')!r}, format='turtle')
why = yaml.safe_load(Path({str(ROOT / 'app/dominios/energia.yaml')!r}).read_text())['preguntas'][0]['porque']
def query(text, domain):
    result = graph.query(text)
    return [str(v) for v in result.vars], [[str(v) if v is not None else None for v in row] for row in result]
with patch.object(dominio.common, 'run', query):
    show_story('energia', why, ['company', 'share', 'operated'],
               [['CHEVRON', 2000000, 3000000], ['OTRA', 1500000, 2500000]], 'test', {tech!r})
'''
    app = AppTest.from_string(script).run(timeout=20)
    app.toggle[0].set_value(True).run()
    assert not app.exception, [e.message for e in app.exception]
    # Volumes in the business view are in millions of m³
    assert any('3,00 millones de m³' in item.value and '1,50 millones de m³' in item.value for item in app.info)
    assert [m.value for m in app.metric] == ['3,00 M m³', '2,00 M m³']
    breakdown = next(frame.value for frame in app.dataframe if len(frame.value) == 2)
    assert set(breakdown['Concesión']) == {'LOMA CAMPANA', 'OTRA CONCESIÓN'}
    assert sum(float(value.replace(',', '.')) for value in breakdown['Su parte de petróleo (millones de m³)']) == 2
    assert any('pendiente de confirmación humana' in frame.value.to_string() for frame in app.dataframe)
    app.selectbox[0].set_value('OTRA').run()
    assert not app.exception, [e.message for e in app.exception]
    assert any('OTRA' in item.value for item in app.info)
    assert [m.value for m in app.metric] == ['2,50 M m³', '1,50 M m³']
