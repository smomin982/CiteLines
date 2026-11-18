"""Independent oracle, sampling frame, and exported-result integrity."""
import csv
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from research.closure_study import choose_pairs
from route_map import Citation, CitationNetwork


def test_pair_ranks_cover_unequal_components_once():
    groups = [["1","2"], ["3","4","5","6"]]
    total, pairs = choose_pairs(groups, 7, 507)
    assert total == len(set(pairs)) == 7
    assert set(pairs) == {p for group in groups for p in combinations(group, 2)}


def test_exhaustive_simple_path_oracle():
    # All 512 possible three-post, three-page networks. DFS enumerates simple
    # paths directly from raw edges; it does not call the production BFS.
    possible = [(p,k) for p in "123" for k in "abc"]
    for mask in range(512):
        edges = [e for i,e in enumerate(possible) if mask & (1 << i)]
        net = CitationNetwork((Citation(a,b,"w",b,0) for a,b in edges), 0)
        for closed in (None, "a", "b", "c"):
            allowed = {(x,y) for a,b in edges if b != closed for x,y in ((a,b),(b,a))}
            for start,end in combinations("123",2):
                stack, lengths = [(start,)], []
                while stack:
                    path = stack.pop()
                    if path[-1] == end:
                        lengths.append(len(path))
                    else:
                        stack.extend(path+(v,) for u,v in allowed if u == path[-1] and v not in path)
                actual = net.route(start,end,closed)
                assert (len(actual) if actual else None) == min(lengths, default=None)
                if actual:
                    assert actual[0] == start and actual[-1] == end
                    assert all(edge in allowed for edge in zip(actual,actual[1:]))


def test_published_denominators_match_raw_trials():
    folder = Path(__file__).resolve().parents[1] / "research/study"
    summary = json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    with (folder/"closures.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    pairs, fragile, keys = Counter(), set(), set()
    for row in rows:
        pair = row["origin"],row["destination"]
        key = pair,row["closed_page"]
        assert key not in keys
        keys.add(key)
        pairs[pair] += 1
        backup = row["backup_transfers"]
        if not backup:
            fragile.add(pair)
        assert row["outcome"] == ("disconnected" if not backup else
                                  "unchanged" if backup == row["original_transfers"] else "detour")
        assert not backup or int(backup) >= int(row["original_transfers"])
    assert all(pairs[r["origin"],r["destination"]] == int(r["original_transfers"]) for r in rows)
    assert len(rows) == summary["trials"]
    assert len(pairs) == summary["pairs"] == 500
    assert len(fragile) == summary["fragile_pairs"]
    assert Counter(r["outcome"] for r in rows) == summary["outcomes"]
