"""A domain's screen from its configuration file (app/dominios/<dominio>.yaml).

The same three tabs as oncology: Preguntar, Por qué confiar and Preguntas frecuentes, with the two modes
(business by default, technical with the switch). Everything specific to the domain (questions, columns,
evidence, cards, change scenarios) is in the YAML. One module per part of the screen:

- common.py: What every part of a domain's screen shares: the configuration, cached queries, tables and short texts.
- answers.py: «Preguntar»: an answer with its sources and evidence, «¿Por qué este número?», the demo, claims,
  outside data and questions over texts.
- hood.py: «Bajo el capó» (the technical view): dictionary, mappings, instances as RDF, quality rules, the SPARQL
  console and the map.
- trust_view.py: «Por qué confiar»: the measured evaluation, the change and correction tests and the «sin dato»
  test.
- faq.py: «Preguntas frecuentes» and the glossary.
- screen.py: A domain's whole screen (render): the tabs, in the business or the technical view.

Each module calls another module's functions as module.name (common.run, hood.finding), so every call says
where the function lives, and a test replaces a function there: patch.object(dominio.common, "run", ...).
This file only re-exports the names the rest of the app uses as dominio.<name>.
"""

import answer  # noqa: F401  (tests reach it as dominio.answer)

from .common import (  # noqa: F401
    PROV, load_config, read_json, ayuda, sources, data_version, run, warm_up, prefixed, CHECKS, check_text,
    tabla, md, money, PROV_NS, RDF_TYPE, domain_config, technical, ontology_file, labels, short_iri, sql_table,
    short, validated_questions, llm_status,
)
from .answers import (  # noqa: F401
    as_table, show_answer, explain, show_why, before_after, loaded, show_integration_example, show_demo,
    GRAPHDB, claim_verdict, show_claims, show_external, show_enrichment_saved, text_step, show_text_question,
    company, compare_text_search,
)
from .hood import (  # noqa: F401
    mapping_blocks, ontology_doc, show_pieces, prov_names, instance_graph, show_instances, under_the_hood,
    quality_result, finding, show_quality, show_quality_shacl, sparql_console, GEO, wkt_coords, map_data,
    show_map,
)
from .trust_view import (  # noqa: F401
    show_change_short, show_correction, card_status, trust, show_no_data, evaluation_detail,
)
from .faq import (  # noqa: F401
    glossary, domain_faq, faq_dialog, general_faq, domain_name, show_faq,
)
from .screen import (  # noqa: F401
    render, service_guard,
)
