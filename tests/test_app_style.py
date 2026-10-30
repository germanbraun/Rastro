"""The app's stylesheet (app/estilo.py) targets Streamlit's page markers (data-testid) and its stored-theme key. They are
not a public interface: an upgrade can rename them and the look breaks without an error. Streamlit is pinned, and
this test fails when the installed Streamlit no longer has a marker the stylesheet uses, so an upgrade says what to fix.
"""
import re
from pathlib import Path

import pytest

streamlit = pytest.importorskip("streamlit")

ROOT = Path(__file__).resolve().parents[1]
STYLE = (ROOT / "app/estilo.py").read_text(encoding="utf-8")
BUNDLE = "".join(p.read_text(encoding="utf-8", errors="ignore")
                 for p in (Path(streamlit.__file__).parent / "static").rglob("*.js"))
# Markers Streamlit builds from a prefix and the notice's kind (`stAlertContent${kind}`)
BUILT = {"stAlertContent": ("Error", "Info", "Success", "Warning")}


def test_streamlit_is_the_pinned_version():
    pin = re.search(r"^streamlit==([\d.]+)", (ROOT / "infra/loaders/requirements.txt").read_text(), re.M).group(1)
    assert streamlit.__version__ == pin


@pytest.mark.parametrize("marker", sorted(set(re.findall(r"data-testid=(\w+)", STYLE))))
def test_every_marker_the_stylesheet_uses_exists(marker):
    prefix = next((p for p, kinds in BUILT.items() if marker in {p + k for k in kinds}), None)
    if prefix:
        assert f"{prefix}${{" in BUNDLE, f"Streamlit no longer builds {prefix}<kind>"
    else:
        assert f'"{marker}"' in BUNDLE, f"Streamlit no longer has data-testid {marker}: app/estilo.py needs it"


def test_the_stored_theme_key_is_the_one_removed():
    # KEEP_THEME removes 'stActiveTheme-/-v1' unless it names the app's theme ('Custom Theme')
    assert "stActiveTheme-/-v1" in STYLE and "'Custom Theme'" in STYLE
    assert "stActiveTheme-${window.location.pathname}" in BUNDLE and "CACHED_THEME_VERSION:1" in BUNDLE
    assert '"Custom Theme"' in BUNDLE
