"""What a domain adds to the shared screen with its own code: a model tab, its walkthrough steps, its own demo
moments, the story behind an answer and the numbers of its own slides.

A domain declares its extension in its YAML (`extension: energia.OilAndGas` is the class OilAndGas in
app/extensions/energia/). The shared screen calls the methods below and never imports a domain's code; each method
does nothing by default, so an extension writes only what its domain needs.
"""
import importlib


class Extension:
    def __init__(self, cfg):
        self.cfg = cfg   # the domain's configuration, already in the interface's language

    def has_own_screen(self):
        """Whether the domain draws its whole screen itself instead of the shared template."""
        return False

    def show_screen(self, tech):
        """The domain's whole screen, when it has its own."""

    def has_tab(self):
        """Whether the domain shows a «Rastro Lab» tab."""
        return False

    def show_tab(self, tech):
        """The «Rastro Lab» tab."""

    def example_record(self):
        """The record a walkthrough's {registro_ejemplo} stands for (the model's example)."""
        return None

    def published_run(self):
        """The id a walkthrough's {corrida_publicada} stands for: the model's published run; "" if there is none."""
        return ""

    def show_step(self, step, example, record, tech, key):
        """What a walkthrough step adds after its queries, by the flags in its YAML."""

    def show_demo_moment(self, step, key, tech):
        """A demo moment whose «tipo» the shared screen does not know (a model's prediction, say)."""

    def show_story(self, why, columns, rows, where, tech):
        """The step-by-step story behind an answer, when its «porque» has a «recorrido»."""

    def warm_up(self):
        """Work worth doing in the background when the app opens (training a model, say)."""

    def story_numbers(self, number):
        """The numbers of this domain's own slides, formatted with number(value, decimals)."""
        return {}


def load(cfg):
    """The domain's extension, or None if it declares none."""
    if not cfg.get("extension"):
        return None
    module, name = cfg["extension"].rsplit(".", 1)
    return getattr(importlib.import_module(f"extensions.{module}"), name)(cfg)
