"""Build the January citation database and query minimum-transfer routes."""
import argparse
import csv
import io
import json
import heapq
import sqlite3
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path
from zipfile import ZipFile

from research.pilot import END, START, URL, page
from domains import page_site


@dataclass(frozen=True)
class Citation:
    """Evidence for one edge: a decimal post ID, page key and supporting note."""

    post: str
    key: str
    note: str
    raw: str
    millis: int


def citations(archives):
    """Yield January citations using the pilot's frozen URL rules."""
    for archive in archives:
        with ZipFile(archive) as z:
            member, = [name for name in z.namelist() if name.endswith(".tsv")]
            with z.open(member) as source:
                rows = csv.DictReader(io.TextIOWrapper(source, encoding="utf-8-sig"),
                                      delimiter="\t", quoting=csv.QUOTE_NONE)
                for r in rows:
                    millis = int(r["createdAtMillis"])
                    if not START <= millis < END:
                        continue
                    if not (r["tweetId"].isdigit() and r["noteId"].isdigit()):
                        raise ValueError("Expected decimal post and note IDs")
                    for raw in URL.findall(r["summary"]):
                        raw = raw.rstrip(".,;!?")
                        while raw.endswith(")") and raw.count(")") > raw.count("("):
                            raw = raw[:-1]
                        key = page(raw)
                        if key:
                            yield Citation(r["tweetId"], key, r["noteId"], raw, millis)


def build(db, archives):
    """Create a fresh evidence table; refuse to replace an existing table."""
    with db:
        db.execute("BEGIN")
        db.execute("CREATE TABLE citations(post TEXT, page TEXT, note TEXT, raw TEXT, millis INTEGER,"
                   " PRIMARY KEY(post,page,note,raw))")
        db.executemany("INSERT OR IGNORE INTO citations VALUES(?,?,?,?,?)",
                       ((c.post, c.key, c.note, c.raw, c.millis) for c in citations(archives)))


class CitationNetwork:
    """Snapshot graph. Adjacency is symmetric; every edge has eligible evidence."""

    def __init__(self, records, cutoff):
        self.adj = defaultdict(set)
        self.evidence = {}
        for c in records:
            if c.millis <= cutoff:
                self.adj[c.post].add(c.key)
                self.adj[c.key].add(c.post)
                edge = (c.post, c.key)
                prior = self.evidence.get(edge)
                if prior is None or (c.millis, c.note, c.raw) < (prior.millis, prior.note, prior.raw):
                    self.evidence[edge] = c
        # Sort once so equal-length routes and closure trials are reproducible.
        self.adj = {u: tuple(sorted(vs)) for u, vs in self.adj.items()}

    def nearby(self, start, radius):
        """Map each reachable post (except start) to its minimum 1–2 transfer distance."""
        if radius not in (1, 2):
            raise ValueError("Radius must be one or two transfers")
        if not start.isdigit() or start not in self.adj:
            return {}
        depth = {start: 0}
        queue = deque([start])
        while queue:
            node = queue.popleft()
            if depth[node] == 2 * radius:
                continue
            for nxt in self.adj[node]:
                if nxt not in depth:
                    depth[nxt] = depth[node] + 1
                    queue.append(nxt)
        return {n: d // 2 for n, d in depth.items() if d and d % 2 == 0}

    def closures(self, path):
        """Independently exclude each page on a shortest path; report backup and cost."""
        trials = []
        for key in path[1::2]:
            backup = self.route(path[0], path[-1], key)
            delta = None if backup is None else (len(backup) - len(path)) // 2
            trials.append((key, backup, delta))
        return trials

    @cached_property
    def pages_by_site(self):
        """Index only pages present in this cutoff snapshot."""
        result = defaultdict(set)
        for node in self.adj:
            if not node.isdigit():
                result[page_site(node)].add(node)
        return dict(result)

    def first_connected(self, start, end):
        """Earliest eligible instant and a minimum-transfer path at that instant."""
        if not (start.isdigit() and end.isdigit() and start in self.adj and end in self.adj):
            return None
        first = min(self.evidence[start, page].millis for page in self.adj[start])
        best, queue = {start: first}, [(first, start)]
        while queue:
            stamp, node = heapq.heappop(queue)
            if best[node] != stamp:
                continue
            if node == end:
                return stamp, self.route(start, end, through=stamp)
            for nxt in self.adj[node]:
                edge = (node, nxt) if node.isdigit() else (nxt, node)
                candidate = max(stamp, self.evidence[edge].millis)
                if nxt not in best or candidate < best[nxt]:
                    best[nxt] = candidate
                    heapq.heappush(queue, (candidate, nxt))
        return None

    def route(self, start, end, closed=None, *, through=None, closed_site=None):
        """Return a shortest alternating path, or None for absent/unreachable posts."""
        if not (start.isdigit() and end.isdigit() and start in self.adj and end in self.adj):
            return None
        if through is not None and start == end and all(
            self.evidence[start, key].millis > through for key in self.adj[start]
        ):
            return None
        parent, todo = {start: None}, deque([start])
        blocked = self.pages_by_site.get(closed_site, ()) if closed_site else ()
        while todo:
            u = todo.popleft()
            if u == end:
                path = []
                while u is not None:
                    path.append(u)
                    u = parent[u]
                return path[::-1]
            for v in self.adj[u]:
                if v != closed and v not in parent and v not in blocked:
                    if through is not None:
                        edge = (u, v) if u.isdigit() else (v, u)
                        if self.evidence[edge].millis > through:
                            continue
                    parent[v] = u
                    todo.append(v)
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("database", type=Path)
    ingest.add_argument("archives", nargs=5, type=Path)
    query = commands.add_parser("route")
    query.add_argument("database", type=Path)
    query.add_argument("start")
    query.add_argument("end")
    query.add_argument("--close", help="Exact normalized page URL to exclude")
    query.add_argument("--cutoff", help="Inclusive ISO timestamp with timezone (default: end of January)")
    args = parser.parse_args()
    if args.command == "route" and not args.database.is_file():
        parser.error("Database does not exist; run ingest first")
    db = sqlite3.connect(args.database)
    try:
        if args.command == "ingest":
            build(db, args.archives)
            print("Stored citation records:", db.execute("SELECT COUNT(*) FROM citations").fetchone()[0])
            return
        cutoff = END - 1
        if args.cutoff:
            dt = datetime.fromisoformat(args.cutoff)
            if dt.tzinfo is None:
                parser.error("--cutoff must include a timezone")
            cutoff = int(dt.astimezone(timezone.utc).timestamp() * 1000)
        records = db.execute("SELECT post,page,note,raw,millis FROM citations WHERE millis<=?", (cutoff,))
        graph = CitationNetwork((Citation(*r) for r in records), cutoff)
        path = graph.route(args.start, args.end, args.close)
        proof = []
        for a, b in zip(path or [], (path or [])[1:]):
            c = graph.evidence[(a, b) if a.isdigit() else (b, a)]
            proof.append(dict(note=c.note, raw=c.raw, millis=c.millis))
        print(json.dumps(dict(path=path, transfers=None if path is None else len(path)//2,
                              evidence=proof), indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
