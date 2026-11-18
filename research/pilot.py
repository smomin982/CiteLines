"""Profile January 2025 and find witness routes. Standard library only."""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


URL = re.compile(r"""https?://[^\s<>"'`]+""", re.I)
START, END = (int(datetime(2025, m, 1, tzinfo=timezone.utc).timestamp() * 1000)
              for m in (1, 2))


def page(raw):
    """Conservative URL key; keep meaningful query parameters and path case."""
    try:
        u = urlsplit(raw)
        if not u.hostname or "." not in u.hostname or u.username or u.password:
            return None
        if u.hostname.lower() in {"t.co", "bit.ly", "tinyurl.com", "ow.ly"}:
            return None
        query = "&".join(p for p in u.query.split("&") if not p.lower().startswith("utm_"))
        return urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path or "/", query, ""))
    except ValueError:
        return None


def route(graph, a, b, closed):
    """One shortest path after closing a page, or None."""
    parents, queue = {a: None}, deque([a])
    while queue:
        here = queue.popleft()
        if here == b:
            trail = []
            while here is not None:
                trail.append(here)
                here = parents[here]
            return trail[::-1]
        for nxt in sorted(graph[here]):
            if nxt != closed and nxt not in parents:
                parents[nxt] = here
                queue.append(nxt)
    return None


def run(files):
    counts, manifest = Counter(), []
    graph, evidence = defaultdict(set), {}
    posts, notes = set(), set()
    audits = {"merged": [], "distinct_same_host": []}
    by_host = {}
    for file in files:
        with file.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        with zipfile.ZipFile(file) as z:
            member, = [n for n in z.namelist() if n.endswith(".tsv")]
            rows = jan = 0
            with z.open(member) as stream:
                reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"),
                                        delimiter="\t", quoting=csv.QUOTE_NONE)
                for row in reader:
                    rows += 1
                    stamp = int(row["createdAtMillis"])
                    if not START <= stamp < END:
                        continue
                    jan += 1
                    post, note = row["tweetId"], row["noteId"]
                    assert post.isdigit() and note.isdigit()
                    posts.add(post)
                    notes.add(note)
                    for raw in URL.findall(row["summary"]):
                        raw = raw.rstrip(".,;!?")
                        while raw.endswith(")") and raw.count(")") > raw.count("("):
                            raw = raw[:-1]
                        key = page(raw)
                        if not key:
                            counts["excluded_url_occurrences"] += 1
                            continue
                        edge = post, key
                        graph[post].add(key)
                        graph[key].add(post)
                        record = {"post": post, "page": key, "raw": raw, "note": note,
                                  "created_at_utc": datetime.fromtimestamp(stamp/1000, timezone.utc).isoformat()}
                        evidence.setdefault(edge, record)
                        if raw != key and len(audits["merged"]) < 10:
                            audits["merged"].append([raw, key])
                        host = urlsplit(key).netloc
                        other = by_host.setdefault(host, key)
                        if other != key and len(audits["distinct_same_host"]) < 10:
                            audits["distinct_same_host"].append([other, key])
            manifest.append(dict(member=member, archive_sha256=digest, rows=rows, january_rows=jan))

    pages = sorted(set(graph) - posts)
    shared = [k for k in pages if len(graph[k]) >= 2]
    counts.update(notes=len(notes), posts=len(posts), posts_with_pages=len(graph)-len(pages),
                  pages=len(pages), shared_pages=len(shared), edges=len(evidence),
                  posts_reaching_another=len(set().union(*(graph[k] for k in shared))))
    cases = {}
    # Select readable direct links, then look for a strictly longer bypass.
    for k in sorted(shared, key=lambda k: ("wikipedia.org/wiki/" not in k, len(graph[k]), k)):
        for a, b in combinations(sorted(graph[k]), 2):
            leaf = min(len(graph[a]), len(graph[b])) == 1
            if leaf and "disconnected" in cases:
                continue
            if not leaf and "detour" in cases:
                continue
            alt = route(graph, a, b, k)
            kind = "disconnected" if alt is None else "detour"
            if kind in cases or (alt and not 5 <= len(alt) <= 9):
                continue
            before = [a, k, b]
            witnesses = [evidence[(x, y) if x in posts else (y, x)]
                         for trail in (before, alt or []) for x, y in zip(trail, trail[1:])]
            cases[kind] = dict(before=before, removed=k, after=alt, witnesses=witnesses,
                               endpoint_page_counts=[len(graph[a]), len(graph[b])])
        if len(cases) == 2:
            break
    return dict(snapshot="2026-11-17", window="[2025-01-01, 2025-02-01) UTC", archives=manifest,
                profile=counts, cases=cases, normalization_samples=audits)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("archives", nargs=5, type=Path, help="Five Notes ZIPs in shard order")
    cli.add_argument("--out", type=Path, required=True)
    args = cli.parse_args()
    result = run(args.archives)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["profile"], list(result["cases"]))
