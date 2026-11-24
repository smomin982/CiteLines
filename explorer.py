"""Local, server-rendered citation explorer. Run: python explorer.py january.sqlite"""
import argparse
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from functools import lru_cache
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from route_map import Citation, CitationNetwork
from views import findings, render_view
from layout import frame
from source_view import source_view
from topic_view import topic_view
from contextlib import closing
from post_preview import SCRIPT, preview
from english_posts import collection, english, scope
from interactive_map import CASES as MAP_CASES, SCRIPT as MAP_SCRIPT, examples, map_view

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "data/english_cases.json").read_text(encoding="utf-8"))
FONTS = {f"/assets/fonts/{name}": (ROOT / "assets/fonts" / name).read_bytes()
         for name in ("manrope.woff2", "source-sans-3.woff2")}


def load_network(db, day, english_ids=None):
    cutoff = int(datetime.combine(day, datetime.max.time(), timezone.utc).timestamp() * 1000)
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as conn:
        if english_ids is not None:
            scope(conn,english_ids)
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
    if not params or params.get("mode") == "map":
        day = date.fromisoformat(params.get("day","2025-01-31"))
        if not date(2025,1,1) <= day <= date(2025,1,31):
            raise ValueError("Select a day in January 2025.")
        full = date(2025,1,31)
        graph = snapshot(day)
        _,_,_,a,b = MAP_CASES[0]
        if not params and not graph.route(a,b):
            a,_,b = CASES["space"]["before"]
        return map_view(graph,post_id(params.get("a",a)),post_id(params.get("b",b)),day,
                        examples(graph if day==full else snapshot(full)),params.get("page"))
    if params.get("mode") == "findings":
        summaries = [json.loads((ROOT / "research/study" / f).read_text(encoding="utf-8"))
                     for f in ("summary.json","site_summary.json")]
        for summary in summaries:
            summary["examples"] = {}
        return ('<aside><b>Archived study: all languages.</b> These figures describe the January 2025 '
                'network in the November 17, 2026 export, not the verified English subset you can explore.</aside>'
                +findings(*summaries))
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
    english_ids = collection()
    snapshot = lru_cache(maxsize=1)(lambda day: load_network(db, day, english_ids))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path in FONTS:
                payload = FONTS[url.path]
                self.send_response(200)
                self.send_header("Content-Type", "font/woff2")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if url.path == "/post-preview":
                post = parse_qs(url.query).get("id",[""])[0]
                if not re.fullmatch(r"[0-9]{1,20}", post):
                    self.send_error(400)
                    return
                if post not in english_ids:
                    self.send_error(404,"Not a verified English post")
                    return
                try:
                    item = preview(post)
                    if not english(item["language"]):
                        raise ValueError("No English preview")
                    payload = json.dumps(item).encode()
                except (OSError, ValueError, KeyError):
                    self.send_error(503, "Original post unavailable")
                    return
                self.send_response(200)
                self.send_header("Content-Type","application/json")
                self.send_header("Cache-Control","private, max-age=300")
                self.send_header("Content-Length",str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            if url.path != "/":
                self.send_error(404)
                return
            try:
                params = {k:v[-1] for k,v in parse_qs(url.query).items()}
                for k in ("a","b","first"):
                    if params.get(k) and post_id(params[k]) not in english_ids:
                        raise ValueError("That post is outside the verified English collection.")
                if params.get("mode") == "topics":
                    with closing(sqlite3.connect(db.as_uri()+"?mode=ro",uri=True)) as conn:
                        scope(conn,english_ids)
                        body = topic_view(conn,params)
                else:
                    body = render(params, snapshot)
                code = 200
            except ValueError as exc:
                body, code = f'<p>{escape(str(exc))}</p><a href="/">Reset explorer</a>', 400
            html = frame(body,params.get("mode","route"),SCRIPT+MAP_SCRIPT,len(english_ids)).encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"Open http://127.0.0.1:{args.port}/ (Ctrl+C to stop)", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
