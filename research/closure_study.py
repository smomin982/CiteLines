"""Run from the root: python -m research.closure_study january.sqlite"""
import argparse
import csv
import json
import random
from bisect import bisect_right
from collections import Counter
from datetime import date
from itertools import accumulate
from pathlib import Path

from explorer import load_network


def components(graph):
    """Partition posts into connected components; order independent of SQL row order."""
    seen = set()
    groups = []
    for root in sorted(graph.adj):
        if root in seen:
            continue
        stack, posts = [root], []
        seen.add(root)
        while stack:
            node = stack.pop()
            if node.isdigit():
                posts.append(node)
            for v in graph.adj[node]:
                if v not in seen:
                    stack.append(v)
                    seen.add(v)
        if len(posts) >= 2:
            groups.append(sorted(posts))
    return groups


def choose_pairs(groups, n, seed):
    """Sample distinct ranks uniformly; decode triangular numbers within each component."""
    from math import isqrt
    ends = list(accumulate(len(g)*(len(g)-1)//2 for g in groups))
    total = ends[-1] if ends else 0
    pairs = []
    for rank in random.Random(seed).sample(range(total), n):
        i = bisect_right(ends, rank)
        k = rank - (ends[i-1] if i else 0)
        j = (1 + isqrt(1+8*k))//2
        pairs.append((groups[i][k-j*(j-1)//2], groups[i][j]))
    return total, pairs


def run(db, folder, n=500, seed=507):
    graph = load_network(db.resolve(), date(2025, 1, 31))
    groups = components(graph)
    total, pairs = choose_pairs(groups, n, seed)
    counts, fragile, examples = Counter(), 0, {}
    folder.mkdir(exist_ok=True, parents=True)
    with (folder/"closures.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["origin","destination","original_transfers","closed_page","backup_transfers","outcome"])
        for a, b in pairs:
            path = graph.route(a, b)
            before = len(path)//2
            lost = False
            for url, backup, delta in graph.closures(path):
                kind = "disconnected" if delta is None else "detour" if delta else "unchanged"
                after = len(backup)//2 if backup else None
                writer.writerow([a, b, before, url, after, kind])
                counts[kind] += 1
                lost |= backup is None
                if kind not in examples or before < examples[kind]["transfers"]:
                    examples[kind] = dict(a=a, b=b, closed=url, transfers=before)
            fragile += lost
    summary = dict(seed=seed, pairs=n, eligible_pairs=total, components=len(groups),
                   trials=sum(counts.values()), outcomes=counts, fragile_pairs=fragile,
                   examples=examples)
    (folder/"summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("--out", type=Path, default=Path("research/study"))
    args = parser.parse_args()
    run(args.database, args.out)
