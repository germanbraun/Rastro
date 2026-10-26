"""Retained official company icons must remain usable without network access."""
import base64
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import logos


def test_retained_icons_are_intact_and_work_offline(monkeypatch):
    def offline(*args, **kwargs):
        raise AssertionError('Retained icons must not request the network')
    monkeypatch.setattr(logos, 'remote_icon', offline)
    manifest = json.loads((logos.LOCAL_ICONS / 'manifest.json').read_text())
    for domain, receipt in manifest.items():
        result = logos.icon(domain)
        mime, data = result.split(';base64,')
        assert mime == 'data:' + receipt['mime']
        assert hashlib.sha256(base64.b64decode(data)).hexdigest() == receipt['sha256']
        assert receipt['source_url'].startswith('https://')


def test_unknown_icon_can_remain_blank(monkeypatch):
    monkeypatch.setattr(logos, 'remote_icon', lambda domain: None)
    assert logos.icon('unverified-company.invalid') is None
