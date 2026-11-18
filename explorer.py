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
from urllib.parse import parse_qs, urlencode, urlsplit

from route_map import Citation, CitationNetwork

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "research/january.json").read_text(encoding="utf-8"))["cases"]
BASE = CASES["detour"]["before"]


def load_network(db, day):
    cutoff = int(datetime.combine(day, datetime.max.time(), timezone.utc).timestamp() * 1000)
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as conn:
        rows = conn.execute("SELECT post,page,note,raw,millis FROM citations WHERE millis<=? "
                            "ORDER BY post,page,millis,note,raw", (cutoff,))
        return CitationNetwork((Citation(*r) for r in rows), cutoff)


def post_id(value):
    match = re.fullmatch(r"(?:https?://(?:www\.)?(?:x|twitter)\.com/(?:i/web|[\w]+)/status/)?"
                         r"([0-9]+)(?:[?#].*)?", value.strip())
    if not match:
        raise ValueError("Enter a numeric post ID or a link to an X post.")
    return match[1]


def link(text, **params):
    return f'<a href="?{escape(urlencode(params))}">{escape(text)}</a>'


def itinerary(graph, path):
    if path is None:
        return "<p>No route in this snapshot.</p>"
    rows = []
    for i, item in enumerate(path):
        if i % 2 == 0:
            rows.append(f'<li><b>Post</b> {escape(item)}</li>')
        else:
            citations = [graph.evidence[(p, item)] for p in (path[i-1], path[i+1])]
            notes = "".join(f"<li>Note {escape(c.note)} · "
                            f"{datetime.fromtimestamp(c.millis/1000, timezone.utc):%Y-%m-%d %H:%M} UTC"
                            f"<br>{escape(c.raw)}</li>" for c in citations)
            rows.append(f'<li class="page"><b>Transfer at {escape(urlsplit(item).netloc)}</b>'
                        f'<br><a href="{escape(item)}" target="_blank" rel="noreferrer">{escape(item)}</a>'
                        f'<details><summary>Inspect both citations</summary><ul>{notes}</ul></details></li>')
    return f"<p><strong>{len(path)//2} transfer(s)</strong></p><ol>{''.join(rows)}</ol>"


def render(params, snapshot):
    a, b = post_id(params.get("a", BASE[0])), post_id(params.get("b", BASE[-1]))
    day = date.fromisoformat(params.get("day", "2025-01-31"))
    if not date(2025, 1, 1) <= day <= date(2025, 1, 31):
        raise ValueError("Select a day in January 2025.")
    mode = params.get("mode", "route")
    graph = snapshot(day)
    common = dict(a=a, b=b, day=day.isoformat())
    demos = " · ".join(link(label, a=c["before"][0], b=c["before"][-1], mode="stress")
                       for label, c in (("Real detour", CASES["detour"]),
                                        ("Fragile connection", CASES["disconnected"])))
    form = (f'<nav>Try an example: {demos}</nav><form><label>Origin post ID or URL'
            f'<input name="a" required value="{escape(a)}"></label><label>Destination post ID or URL'
            f'<input name="b" value="{escape(b)}"></label><label>Through date (UTC)'
            f'<input name="day" type="date" min="2025-01-01" max="2025-01-31" value="{day}"></label>'
            '<div><button name="mode" value="route">Find route</button>'
            '<button name="mode" value="nearby">Explore nearby</button>'
            '<button name="mode" value="stress">Stress-test route</button></div></form>')
    if mode == "nearby":
        near = graph.nearby(a, 2)
        body = "<h2>Departures from this post</h2>"
        if a not in graph.adj:
            body += "<p>This origin has no eligible citation by the selected date.</p>"
        for distance in (1, 2):
            ids = sorted(p for p in near if near[p] == distance)
            body += f"<h3>{distance} transfer(s) · {len(ids):,} destinations</h3>"
            body += "<ul>" + "".join("<li>"+link(p, a=a, b=p, day=str(day))+"</li>"
                                     for p in ids[:25]) + "</ul>"
            if len(ids) > 25:
                body += "<small>First 25 IDs shown.</small>"
    else:
        path = graph.route(a, b)
        body = "<h2>Shortest citation route</h2>" + itinerary(graph, path)
        if mode == "stress" and path:
            body += "<h2>What breaks if you pull a source?</h2><p>Each trial closes one page, then restores it before the next trial.</p>"
            if len(path) == 1:
                body += "<p>No page to close on a zero-transfer route.</p>"
            for key, backup, delta in graph.closures(path):
                label = ("Disconnected" if delta is None else "Equal-length backup" if delta == 0
                         else f"Detour: +{delta} transfer(s)")
                body += f"<article><strong>{label}</strong><p>Removed: {escape(key)}</p>"
                body += "<details><summary>Inspect closure result</summary>" + itinerary(graph, backup) + "</details></article>"
        elif mode == "route" and path and len(path) > 1:
            body += link("Test every page on this route →", mode="stress", **common)
    return form + body


STYLE = """body{font:16px/1.55 system-ui;background:#f7f6ef;color:#152d32;margin:0}
main{max-width:850px;margin:auto;padding:2em}header{border-bottom:4px solid #178072}
h1{font-size:2.7em;margin:.1em 0}nav,form,article{background:white;padding:1em;margin:1em 0}
form{display:flex;flex-wrap:wrap;gap:1em}label{font-size:.85em}input{display:block;padding:.5em}
button{background:#175953;color:white;padding:.6em;border:0;margin:.2em;cursor:pointer}
a{color:#095c70}li,p{overflow-wrap:anywhere}.page{border-left:4px solid #168879;padding:.6em}
details{margin:.5em 0}summary{cursor:pointer}small{color:#475b60}"""


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
                    '<main><header><small>COMMUNITY NOTES · JANUARY 2025</small><h1>CiteLines</h1>'
                    '<p>Follow the citations. Find the page holding a connection together.</p></header>'
                    + body + '<hr><small>Connections show citation reuse in this snapshot, not agreement or influence.</small></main></html>').encode()
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
