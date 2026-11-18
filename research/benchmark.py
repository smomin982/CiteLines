"""Compare two prepared graph representations on identical January prefixes."""
import csv
import sqlite3
import sys
from collections import defaultdict, deque
from itertools import combinations
from pathlib import Path
from statistics import median
from time import perf_counter

from research.closure_study import choose_pairs, components
from route_map import Citation, CitationNetwork, START


def projected(records):
    by_page = defaultdict(set)
    for c in records:
        by_page[c.key].add(c.post)
    neighbors = defaultdict(dict)
    for key, posts in by_page.items():
        for a, b in combinations(posts, 2):
            sources = neighbors[a].setdefault(b, set())
            sources.add(key)
            neighbors[b][a] = sources
    return neighbors


def distance(adj, a, b, closed):
    seen, work = {a}, deque([(a, 0)])
    while work:
        node, depth = work.popleft()
        if node == b:
            return depth
        for v, pages in adj[node].items():
            if v not in seen and (len(pages) > 1 or closed not in pages):
                seen.add(v)
                work.append((v, depth+1))
    return None


def run(db):
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["days","records","bipartite_edges","projected_edges","bipartite_build_ms",
                     "projected_build_ms","bipartite_closure_median_ms","projected_closure_median_ms"])
    with sqlite3.connect(db.as_uri()+"?mode=ro", uri=True) as conn:
        for days in (1, 3, 7, 14, 31):
            cutoff = START + days*86400000 - 1
            rows = [Citation(*r) for r in conn.execute(
                "SELECT post,page,note,raw,millis FROM citations WHERE millis<=?", (cutoff,))]
            t = perf_counter()
            graph = CitationNetwork(rows, cutoff)
            btime = perf_counter()-t
            t = perf_counter()
            adj = projected(rows)
            ptime = perf_counter()-t
            _, pairs = choose_pairs(components(graph), 32, 507)
            bt, pt = [], []
            for a, b in pairs:
                closed = graph.route(a,b)[1]
                t = perf_counter()
                route = graph.route(a,b,closed)
                bt.append(perf_counter()-t)
                t = perf_counter()
                result = distance(adj,a,b,closed)
                pt.append(perf_counter()-t)
                assert result == (len(route)//2 if route else None)
            times = [btime, ptime, median(bt), median(pt)]
            writer.writerow([days,len(rows),len(graph.evidence),sum(map(len,adj.values()))//2,
                             *(round(1000*x, 3) for x in times)])


if __name__ == "__main__":
    run(Path(sys.argv[1]).resolve())
