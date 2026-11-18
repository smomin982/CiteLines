"""Local, server-rendered citation explorer. Run: python explorer.py january.sqlite"""
import argparse
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from functools import lru_cache
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from route_map import Citation, CitationNetwork
from views import STYLE, findings, render_view
from source_view import source_view

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "research/january.json").read_text(encoding="utf-8"))["cases"]
BASE = CASES["detour"]["before"]


def load_network(db, day):
    cutoff = int(datetime.combine(day, datetime.max.time(), timezone.utc).timestamp() * 1000)
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as conn:
        enriched = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='note_text'").fetchone()
        extra = ",summary" if enriched else ""
        join = " LEFT JOIN note_text USING(note)" if enriched else ""
        rows = conn.execute(f"SELECT post,page,note,raw,millis{extra} FROM citations{join} WHERE millis<=? "
                            "ORDER BY post,page,millis,note,raw", (cutoff,))
        return CitationNetwork((Citation(*r) for r in rows), cutoff)


def post_id(value):
    match = re.fullmatch(r"(?:https?://(?:www\.)?(?:x|twitter)\.com/(?:i/web|[\w]+)/status/)?"
                         r"([0-9]+)(?:[?#].*)?", value.strip())
    if not match:
        raise ValueError("Enter a numeric post ID or a link to an X post.")
    return match[1]


def render(params, snapshot):
    if params.get("mode") == "findings":
        return findings(*(json.loads((ROOT / "research/study" / f).read_text(encoding="utf-8"))
                          for f in ("summary.json","site_summary.json")))
    if params.get("mode") in {"sources", "source_pair"}:
        day = date.fromisoformat(params.get("day","2025-01-31"))
        if not date(2025,1,1) <= day <= date(2025,1,31):
            raise ValueError("Select a day in January 2025.")
        graph = snapshot(day)
        if params["mode"] == "sources":
            return source_view(graph, params, day)
        a,b = (post_id(params.get(k,"")) for k in ("a","b"))
        if a == b or any((p,params.get("page")) not in graph.evidence for p in (a,b)):
            raise ValueError("Select two different posts that cite this page by the chosen date.")
        params = dict(params, mode=params.get("action","compare"))
    return render_view(params, snapshot, CASES, post_id)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("database", type=Path)
    cli.add_argument("--port", type=int, default=8765)
    args = cli.parse_args()
    db = args.database.resolve()
    if not db.is_file():
        cli.error("Database not found. Build it with route_map.py ingest first.")
    snapshot = lru_cache(maxsize=1)(lambda day: load_network(db, day))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path != "/":
                self.send_error(404)
                return
            try:
                body = render({k: v[-1] for k, v in parse_qs(url.query).items()}, snapshot)
                code = 200
            except ValueError as exc:
                body, code = f'<p>{escape(str(exc))}</p><a href="/">Reset explorer</a>', 400
            html = (f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" '
                    f'content="width=device-width,initial-scale=1"><title>CiteLines</title><style>{STYLE}</style>'
                    '<main><header><small>CiteLines / January 2025</small><h1>What connects two posts on X?</h1>'
                    '<p>People write <b>Community Notes</b> to add context to posts on X. When notes on two posts link to the same page, '
                    'CiteLines draws a connection. Follow one below, then see what happens without that source.</p>'
                    '<nav><a href="/">Explore a route</a> · <a href="?mode=sources">Explore by source</a> · <a href="?mode=findings">What we found</a></nav></header>'
                    + body + '<footer>Based on proposed notes in the January snapshot. A shared source does not imply agreement or influence.</footer></main></html>').encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

    with HTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Open http://127.0.0.1:{args.port}/ (Ctrl+C to stop)", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
