"""A route switch cannot change endpoints or test a different page inadvertently."""
from datetime import date
import re
import sqlite3
from contextlib import closing

from explorer import load_network
from interactive_map import examples, map_view
from route_map import Citation, CitationNetwork


def test_map_keeps_pair_fixed_and_distinguishes_single_page_from_site():
    primary = "https://news.example.org/primary"
    left = "https://other.example.net/left"
    right = "https://docs.example.org/right"
    rows = [("1",primary), ("2",primary), ("1",left), ("3",left), ("3",right), ("2",right)]
    graph = CitationNetwork((Citation(p,k,p,k,1,"Witness "+p) for p,k in rows),1)
    text = map_view(graph,"1","2",date(2025,1,31),"")
    sections = dict(re.findall(r'<template data-result="([^"]+)">(.*?)</template>',text))
    assert "1 shared page" in sections["0-original"]
    assert 'data-map-node="0"' in sections["0-original"]
    assert "2 shared pages" in sections["0-page"] and sections["0-page"].count("New ·") == 2
    assert "Disconnected" in sections["0-site"]
    assert re.findall(r'class="xcard" data-post="([0-9]+)"',text) == ["1","2"]
    assert "Witness 1" in text and "Witness 2" in text


def test_case_library_omits_outcomes_that_no_longer_hold(monkeypatch):
    k = "https://example.org/story"
    monkeypatch.setattr("interactive_map.CASES",(
        ("detour","Needs a detour","Topic","1","2"),("broken","Connection breaks","Topic","1","2")))
    graph = CitationNetwork([Citation(p,k,p,k,1) for p in ("1","2")],1)
    html = examples(graph)
    assert "Connection breaks" in html and "Needs a detour" not in html


def test_loaded_snapshot_does_not_hold_database_open(tmp_path):
    path = tmp_path/"map.sqlite"
    with closing(sqlite3.connect(path)) as db:
        db.execute("CREATE TABLE citations(post,page,note,raw,millis)")
        db.executemany("INSERT INTO citations VALUES(?,?,?,?,?)",
                       [(p,"https://example.org",p,"https://example.org",1) for p in ("1","2")])
        db.commit()
    graph = load_network(path,date(2025,1,31),["1","2"])
    path.unlink()
    assert graph.route("1","2") == ["1","https://example.org","2"]
