"""Do not misattribute contributor text or provider markup to the author."""
from io import BytesIO
import json

import pytest

import post_preview


def test_public_preview_keeps_unicode_and_linebreaks_and_excludes_attribution(monkeypatch):
    doc = {"author_name":"Example", "html":'<blockquote><p lang="de">Über <a href="#">X</a>'
           '<br>eins &amp; zwei</p>— Someone <a>January 24, 2025</a></blockquote>'}
    monkeypatch.setattr(post_preview, "urlopen", lambda *a,**kw: BytesIO(json.dumps(doc).encode()))
    assert post_preview.fetch_preview("123", -5) == {
        "author":"Example","text":"Über X\neins & zwei","date":"January 24, 2025"}


def test_absent_text_does_not_become_a_fake_post(monkeypatch):
    monkeypatch.setattr(post_preview, "urlopen", lambda *a,**kw: BytesIO(b'{"html":"Unavailable"}'))
    with pytest.raises(ValueError):
        post_preview.fetch_preview("456",-5)
    with pytest.raises(ValueError):
        post_preview.preview("https://not-a-post.example/")
