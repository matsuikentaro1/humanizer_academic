"""Render assets/banner.png from banner.html.

Edit the version and pattern count in banner.html, then run:
    python assets/banner-src/render.py
Requires Playwright with Chromium (pip install playwright && playwright install chromium).
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

here = Path(__file__).parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else here.parent / "banner.png"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 400}, device_scale_factor=2)
    page.goto((here / "banner.html").as_uri())
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    page.locator(".banner").screenshot(path=str(out), omit_background=True)
    browser.close()
print(out)
