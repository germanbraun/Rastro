"""A backup of the live demo, for when it cannot run (no network, a stopped service, a borrowed laptop): the app's
Demo tab, moment by moment, as screenshots in the repo (docs/respaldo/<lang>/) and as a video outside it
(data/raw/respaldo/, not versioned: a few MB that change on every capture).

It reads the running app (docker compose up -d) like a person would: it opens the Demo tab, waits until each moment
has finished running, takes the whole screen, scrolls through it slowly for the video and presses «Siguiente». Run it
again whenever a number of the demo changes, and look at the screenshots before committing them.

    python3 -m pip install playwright      # once; it drives the Google Chrome already installed
    python3 docs/respaldo/capturar.py [--lang es|en] [--url http://localhost:8501]
"""
import argparse
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
WIDTH, HEIGHT = 1440, 900
MAIN = "[data-testid=stMain]"


def settle(page):
    """Waits until Streamlit has finished running the page: its «running» indicator gone and nothing still loading."""
    page.wait_for_timeout(1500)
    page.wait_for_function("!document.querySelector('[data-testid=stStatusWidget]')", timeout=180_000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)


def whole(page, path):
    """Streamlit scrolls inside its main block, so the whole moment needs a window as tall as the moment."""
    height = page.evaluate(f"document.querySelector('{MAIN}').scrollHeight")
    page.set_viewport_size({"width": WIDTH, "height": height})
    page.wait_for_timeout(800)
    page.screenshot(path=path)
    page.set_viewport_size({"width": WIDTH, "height": HEIGHT})


def capture(lang, url):
    shots = Path(__file__).parent / lang
    video = ROOT / "data/raw/respaldo"
    shutil.rmtree(shots, ignore_errors=True)
    shots.mkdir(parents=True)
    video.mkdir(parents=True, exist_ok=True)
    next_label = {"es": "Siguiente →", "en": "Next →"}[lang]
    why_label = {"es": "¿Por qué este número?", "en": "Why this number?"}[lang]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        context = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, locale=lang,
                                      record_video_dir=str(video), record_video_size={"width": WIDTH, "height": HEIGHT})
        page = context.new_page()
        page.goto(f"{url}/?inicio=demo&lang={lang}")
        page.wait_for_selector(MAIN, timeout=60_000)
        settle(page)
        n = 1
        while True:
            print(f"{n}: {page.locator('h3').first.inner_text()}")
            height = page.evaluate(f"document.querySelector('{MAIN}').scrollHeight")
            for y in range(0, height, 300):   # the video scrolls through the moment as a presenter would
                page.evaluate(f"document.querySelector('{MAIN}').scrollTo(0, {y})")
                page.wait_for_timeout(700)
            page.evaluate(f"document.querySelector('{MAIN}').scrollTo(0, 0)")
            whole(page, shots / f"momento-{n}.png")
            why = page.get_by_text(why_label, exact=True)
            if why.count():   # the answer's evidence, as the script opens it in moment 1
                why.first.click()
                settle(page)
                whole(page, shots / f"momento-{n}-por-que.png")
            forward = page.get_by_role("button", name=next_label)
            if not forward.count():
                break
            forward.click()
            settle(page)
            n += 1
        context.close()
        page.video.save_as(video / f"demo-{lang}.webm")
        page.video.delete()
        browser.close()
    print(f"{n} moments in {shots.relative_to(ROOT)}/, video in {(video / f'demo-{lang}.webm').relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lang", default="es", choices=("es", "en"))
    parser.add_argument("--url", default="http://localhost:8501")
    args = parser.parse_args()
    capture(args.lang, args.url)
