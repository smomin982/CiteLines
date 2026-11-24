"""A topic result must be supported by the same note as the page citation."""
import sqlite3
from zipfile import ZipFile

import pytest

from english_posts import scope
from route_map import START, build
from topic_search import excerpt, matched_posts, ranked_pages
from topic_view import topic_view


@pytest.fixture
def db(tmp_path):
    notes = [
        ("1","10",0,"Red fox observed https://example.org/a"),
        ("1","11",1,"Another RED FOX https://example.org/a https://example.org/b"),
        ("1","12",0,"Not the same note https://example.org/unrelated"),
        ("2","20",86400000,"The red fox <tag> https://example.org/a"),
        ("3","30",0,"Only an address https://example.org/red-fox"),
        ("4","40",0,"Red, quick fox https://example.org/c"),
    ]
    archive = tmp_path/"notes.zip"
    with ZipFile(archive,"w") as z:
        z.writestr("notes.tsv","tweetId\tnoteId\tcreatedAtMillis\tsummary\n"+
                   "".join(f"{p}\t{n}\t{START+t}\t{s}\n" for p,n,t,s in notes))
    conn = sqlite3.connect(":memory:")
    build(conn,[archive])
    yield conn
    conn.close()


def test_same_note_literal_phrase_counts_and_cutoff(db):
    a,b = "https://example.org/a","https://example.org/b"
    def counts(t):
        return [(k,n) for k,n,_ in ranked_pages(db,"red fox",t)]
    assert counts(START+86399999) == [(a,1),(b,1)]
    assert counts(START+86400000) == [(a,2),(b,1)]
    assert not ranked_pages(db,"fox OR observed",START+86400000)
    assert not ranked_pages(db,"unrelated",START+86400000)
    posts = matched_posts(db,"red fox",START+86400000,a)
    assert [p for p,_ in posts] == ["1","2"]
    assert excerpt(db,"red fox",posts[1][1])[0] == "20"


def test_topic_drilldown_uses_matching_witnesses_and_preserves_date(db):
    args = dict(q="red fox", page="https://example.org/a",first="1",day="2025-01-02")
    view = topic_view(db,args)
    assert "Compare page vs. site" in view and "Connection history" in view
    assert "day=2025-01-02" in view and "a=1&amp;b=2" in view
    assert "&lt;tag&gt;" in view and "<tag>" not in view
    with pytest.raises(ValueError):
        topic_view(db,dict(args,first="3"))


def test_ranked_result_embeds_witness_post_not_note_or_other_matching_post(db):
    view = topic_view(db,dict(q="red fox",day="2025-01-02"))
    assert view.count('data-embed-post="1"') == 2
    assert 'data-embed-post="10"' not in view and 'data-embed-post="2"' not in view
    assert "Note 10" in view and "Note 11" in view


def test_suggestions_count_only_eligible_posts_and_recover_from_early_cutoff(db,monkeypatch):
    monkeypatch.setattr("topic_view.GROUPS",{"Test":["red fox","quick fox","absent"]})
    start = topic_view(db,dict(day="2025-01-01"))
    assert "red fox · 1" in start and "quick fox · 1" in start and "absent" not in start
    month = topic_view(db,{})
    assert "red fox · 2" in month
    early = topic_view(db,dict(day="2025-01-01",q="fox tag"))
    assert "Search the full month: 1 matching post(s)" in early
    partial = topic_view(db,dict(day="2025-01-01",q="red fox"))
    assert "Search the full month →" in partial
    scope(db,["1"])
    filtered = topic_view(db,{})
    assert "red fox · 1" in filtered and "quick fox" not in filtered
    assert "Search the full month:" not in topic_view(db,dict(day="2025-01-01",q="fox tag"))
