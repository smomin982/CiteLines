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
        "author":"Example","text":"Über X\neins & zwei","date":"January 24, 2025","language":"de"}


def test_absent_text_does_not_become_a_fake_post(monkeypatch):
    monkeypatch.setattr(post_preview, "urlopen", lambda *a,**kw: BytesIO(b'{"html":"Unavailable"}'))
    with pytest.raises(ValueError):
        post_preview.fetch_preview("456",-5)
    with pytest.raises(ValueError):
        post_preview.preview("https://not-a-post.example/")


def test_english_labels_and_filtered_graph_do_not_use_note_language():
    import sqlite3
    from english_posts import english, scope
    from route_map import Citation, CitationNetwork
    assert english("en") and english("en-GB")
    assert not any(english(tag) for tag in ("de","ar","und",""))
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE citations(post,page,note,raw,millis)")
        db.executemany("INSERT INTO citations VALUES(?,?,?,?,?)",
                       [(p,k,p,k,1) for p,k in [("1","a"),("2","a"),("2","b"),("3","b")]])
        scope(db,["1","3"])
        graph = CitationNetwork((Citation(*row) for row in db.execute("SELECT * FROM citations")),1)
        assert graph.route("1","3") is None  # Excluding only endpoints would leak post 2.
        assert len(list(db.execute("SELECT * FROM main.citations"))) == 4
