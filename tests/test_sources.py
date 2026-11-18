"""Search counts posts, not duplicate notes; closure follow-up keeps the original sample."""
import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from explorer import render
from route_map import Citation, CitationNetwork


def snap(day):
    rows = [("1","a",1),("1","a",2),("2","a",1),("1","b",1),("2","b",1),("3","b",3)]
    return CitationNetwork((Citation(n,"https://demo.org/"+p,str(i),p,t)
                            for i,(n,p,t) in enumerate(rows)),day.day)


def test_site_ranking_exact_url_and_selected_nondefault_shared_page():
    view = render(dict(mode="sources",q="demo.org"),snap)
    assert view.index("3 citing posts") < view.index("2 citing posts")
    detail = render(dict(mode="sources",q="https://DEMO.ORG/b?utm_source=trial",day="2025-01-02"),snap)
    assert "2 distinct citing posts" in detail and "3 distinct citing posts" not in detail
    args = dict(mode="source_pair",a="1",b="2",page="https://demo.org/b")
    assert "One page or the whole site?" in render(args,snap)
    with pytest.raises(ValueError):
        render(dict(args,b="3",day="2025-01-02"),snap)


def test_site_trials_match_surviving_page_trials_exactly():
    folder = Path(__file__).resolve().parents[1]/"research/study"
    def read(name):
        with (folder/name).open(encoding="utf-8",newline="") as f:
            return list(csv.DictReader(f))
    expected = [r for r in read("closures.csv") if r["backup_transfers"]]
    actual = read("site_closures.csv")
    summary = json.loads((folder/"site_summary.json").read_text())
    assert [{k:r[k] for k in expected[0]} for r in actual] == expected
    assert len(expected) == summary["trials"]
    assert Counter(r["site_outcome"] for r in actual) == summary["outcomes"]
    for r in actual:
        d = r["site_transfers"]
        assert not d or int(d) >= int(r["backup_transfers"])
        assert r["site_outcome"] == ("lost" if not d else "same_length" if d == r["backup_transfers"] else "longer")
