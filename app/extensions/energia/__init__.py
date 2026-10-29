"""Oil and gas: what this domain shows with its own code.

- Rastro Lab, the gas model of new Vaca Muerta wells with and without Rastro (lab/gas/modelo.py): the tab in lab.py,
  with lab_walkthrough.py and lab_alternative.py.
- story.py: the «Paso a paso» of the first answer (how a company's share is calculated, concession by concession).
- correction.py: the correction test as the demo shows it.

They are imported only when used, because loading the model's data takes a while.
"""
import streamlit as st

from dominio import answers, common
from dominio.extension import Extension


class OilAndGas(Extension):
    def has_tab(self):
        return True

    def show_tab(self, tech):
        from . import lab, lab_alternative
        cfg, example = self.cfg, self.cfg.get("ejemplo_lab")
        # The experimental alternative models are a technical detail: the business view keeps the regression
        choice = lab_alternative.select_model(cfg["alternative_lab"]) if cfg.get("alternative_lab") and tech else "ridge"
        pozo = lab.select_well(example) if example else None
        if choice == "alternative":
            lab_alternative.show_alternative(tech, pozo, cfg["alternative_lab"], example)
            return
        # Business view: the three numbers, the well, then «Paso a paso» and how it is calculated
        run_status = lab.show_run_status(pozo, example, tech) if example else {}
        lab.show_lab(tech, pozo=pozo, note=run_status.get("note", ""))
        if example:
            with st.expander(example["titulo"]):
                answers.show_integration_example(example, cfg["domain"], tech, key=f"{cfg['domain']}_lab", record=pozo,
                                                 run_id=run_status["run_id"], ext=self)
        lab.show_how(tech)

    def example_record(self):
        from . import lab
        return lab.modelo.pozo_ejemplo(lab.datos()[1])

    def published_run(self):
        from . import lab
        snapshot = lab.published_snapshot()
        return snapshot["run"]["id"] if snapshot else ""

    def show_step(self, step, example, record, tech, key):
        from . import lab
        if step.get("entrada_pozo"):
            lab.show_input_row(record, example, tech)
        if step.get("calculo_pozo"):
            lab.show_calculation(pozo=record, config=example, tech=tech)
        if step.get("evidencia_pozo"):
            st.markdown(example["ui"]["current_evidence_title"])
            common.tabla(lab.current_evidence(record).rename(columns=example["ui"]["evidence_columns"]),
                         key=f"{key}_current_evidence")

    def show_demo_moment(self, step, key, tech):
        from .correction import show_correction
        if step.get("tipo") == "lab":
            from . import lab
            lab.show_well(key=f"{key}_pozo", pozo=self.example_record())
            if step.get("correccion"):   # the correction told in Rastro Layer, as it reached the model
                show_correction(common.read_json(self.cfg["correccion"]), tech, part="lab")
        elif step.get("tipo") == "correccion":
            show_correction(common.read_json(self.cfg["correccion"]), tech, part=step.get("parte"))

    def show_story(self, why, columns, rows, where, tech):
        from .story import show_story
        show_story(self.cfg["domain"], why, columns, rows, where, tech)

    def warm_up(self):
        from . import lab
        lab.datos()

    def story_numbers(self, number):
        from . import lab
        result = lab.calcular()
        r, (doubtful, tested), start = result[3], result[5], result[8]
        return dict(error_a=number(r["A"]["error"], 1), error_b=number(r["B"]["error"], 1),
                    dudosos=number(doubtful, 0), probados=number(tested, 0),
                    con_fractura=number(start["con_fractura"], 0), tarde=number(start["tarde"], 0))
