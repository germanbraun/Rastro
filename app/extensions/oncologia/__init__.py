"""Oncology: its own screen (screen.py), older than the shared template and kept as it is."""
from dominio.extension import Extension


class Oncology(Extension):
    def has_own_screen(self):
        return True

    def show_screen(self, tech):
        from . import screen
        screen.show(tech)
