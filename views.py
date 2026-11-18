"""Visitor-facing labels and views. Case captions describe notes, not unseen posts."""
from datetime import date, datetime, timezone
from html import escape
from urllib.parse import unquote, urlencode, urlsplit


CAPTIONS = {
    "1882827830331085172": "A note about parties voting together",
    "1884646064566796739": "A note about majority decisions",
    "1882791142183592080": "Notes about seats and party cooperation",
    "1877374179705487627": "A note identifying the pictured sultan",
    "1877389658193277027": "Another note identifying the pictured sultan",
}


def title(url):
    parts = urlsplit(url)
    if url == "https://de.m.wikipedia.org/wiki/Demokratie":
        return "Demokratie · German Wikipedia"
    if "sitzverteilung_20wp" in parts.path:
        return "Seat distribution · German Bundestag"
    if "cdu-weist-vergiftete-weidel" in parts.path:
        return "Report on party cooperation · Frankfurter Rundschau"
    if "ar.m.wikipedia.org" == parts.netloc and "سعيد_بن_سلطان" in unquote(parts.path):
        return "Biography of Said bin Sultan · Arabic Wikipedia"
    slug = unquote(parts.path.rstrip("/").split("/")[-1]).replace("_", " ").replace("-", " ")
    return f"{slug[:85]} · {parts.netloc}" if slug else parts.netloc or url


def link(text, **params):
    anchor = "#outcomes" if params.get("mode") == "stress" else ""
    return f'<a href="?{escape(urlencode(params))}{anchor}">{escape(text)}</a>'


def chain(g, path):
    if not path:
        return "<p>There is no chain of shared pages between these posts by this date.</p>"
    nodes = []
    for i, item in enumerate(path):
        if i % 2 == 0:
            role = "Starting post" if i == 0 else "Destination post" if i == len(path)-1 else "Connecting post"
            caption = CAPTIONS.get(item, "Post on X")
            nodes.append(f'<li class="post"><small>{role}</small><b>{escape(caption)}</b>'
                         f'<a href="https://x.com/i/web/status/{escape(item)}" target="_blank" rel="noreferrer">View post on X ↗</a></li>')
        else:
            cites = [g.evidence[p, item] for p in (path[i-1], path[i+1])]
            proof = "".join(f"<li>Post {escape(c.post)} · note {escape(c.note)} · "
                            f"{datetime.fromtimestamp(c.millis/1000, timezone.utc):%d %b %Y} UTC"
                            f"<br>{escape(c.raw)}</li>" for c in cites)
            nodes.append(f'<li class="source"><small>Both posts cite</small>'
                         f'<b><a href="{escape(item)}" target="_blank" rel="noreferrer">{escape(title(item))}</a></b>'
                         f'<details><summary>Inspect both citations</summary><ul>{proof}</ul></details></li>')
    return '<ol class="chain">' + "".join(nodes) + '</ol>'


def render_view(params, snapshot, cases, parse_id):
    base = cases["detour"]["before"]
    a = parse_id(params.get("a", base[0]))
    mode = params.get("mode", "route")
    b = parse_id(params.get("b") or base[-1]) if mode != "nearby" else base[-1]
    day = date.fromisoformat(params.get("day", "2025-01-31"))
    if not date(2025, 1, 1) <= day <= date(2025, 1, 31):
        raise ValueError("Select a day in January 2025.")
    g = snapshot(day)
    common = dict(a=a, b=b, day=str(day))
    example = next((k for k, c in cases.items() if c["before"][::2] == [a, b]), None)
    controls = (f'<details class="search"><summary>Search your own posts or change the date</summary><form>'
                f'<label>Starting X post URL or ID<input required name="a" value="{escape(a)}"></label>'
                f'<label>Destination (for a route)<input name="b" value="{escape(b)}"></label>'
                f'<label>Include notes through (UTC)<input type="date" name="day" value="{day}" min="2025-01-01" max="2025-01-31"></label>'
                '<button name="mode" value="route">Connect these posts</button><button name="mode" value="nearby">Explore from the start</button></form></details>')
    if mode == "nearby":
        body = ('<small>Explore a neighborhood</small><h2>Which posts are connected to this one?</h2>'
                f'<p>Starting point: <strong>{escape(CAPTIONS.get(a, "Your selected X post"))}</strong>. '
                'Select a result to see the sources that connect it.</p>')
        near = g.nearby(a, 2)
        if not near:
            body += "<p>No other posts are reachable within two shared pages by this date.</p>"
        for dist, heading in ((1, "Share a page directly"), (2, "Connected through one other post")):
            ids = sorted(n for n, d in near.items() if d == dist)
            body += f"<h3>{heading} <span>({len(ids):,})</span></h3>"
            for n in ids[:25]:
                path = g.route(a, n)
                sources = " → ".join(title(s) for s in path[1::2])
                witness = g.evidence[n, path[-2]]
                label = CAPTIONS.get(n, "Note citing " + title(path[-2]))
                body += ('<div class="result">'+link(label, a=a, b=n, day=str(day))+
                         f'<br><small>Via {escape(sources)} · {datetime.fromtimestamp(witness.millis/1000,timezone.utc):%d %b} · post …{escape(n[-6:])}</small></div>')
            if len(ids) > 25:
                body += "<p>Showing the first 25 destinations.</p>"
    else:
        path = g.route(a, b)
        heading, intro = {
            "detour": ("Two posts, one Wikipedia article", "One note discusses parties voting together in Germany. Another discusses majority decisions. Both cite the same German Wikipedia article: <em>Demokratie</em>."),
            "disconnected": ("Two notes identify the same sultan", "On two different posts, contributors identified a pictured person as Said bin Sultan. Both pointed readers to the same Arabic Wikipedia biography."),
        }.get(example, ("How are these posts connected?", "Follow the chain below. Each shared page is cited in notes on the posts immediately above and below it."))
        body = f'<small>{"Guided example" if example else "Your search"} · through {day:%d %B %Y}</small><h2>{heading}</h2><p>{intro}</p>'
        body += chain(g, path)
        if path and len(path) > 1 and mode != "stress":
            text = "Remove that page and see what happens →" if len(path)==3 else "Try removing each shared page →"
            body += '<div class="action">'+link(text, mode="stress", **common)+'</div>'
        elif mode == "stress" and path:
            body += '<h3 id="outcomes">What changed?</h3>'
            if len(path) == 1:
                body += '<p>You selected the same post twice. There is no shared page to remove.</p>'
            for key, backup, delta in g.closures(path):
                label = "Disconnected" if delta is None else "Equal-length backup" if not delta else f"Detour: +{delta}"
                verdict = ("This page held the connection together." if delta is None else
                           "Another route is just as short." if not delta else "The connection survives, but takes a longer route.")
                detail = ("No chain remains in this snapshot." if backup is None else
                          f"The shortest chain now uses {len(backup)//2} shared pages instead of {len(path)//2}.")
                body += f'<article class="outcome"><small>{escape(label)} · single-page experiment</small><h3>{verdict}</h3><p>With <b>{escape(title(key))}</b> removed: {detail}</p>'
                if backup:
                    body += '<details open><summary>Follow the backup route</summary>'+chain(g, backup)+'</details>'
                body += '</article>'
        body += '<p>'+link("Explore other posts connected to the starting post →", mode="nearby", **common)+'</p>'
    demos = " &nbsp;·&nbsp; ".join(link(label, a=c["before"][0], b=c["before"][-1])
                                   for label,c in (("German voting debate",cases["detour"]),("A sultan’s portrait",cases["disconnected"])))
    return '<section class="story">'+body+'</section><aside><b>Try a case:</b> '+demos+'</aside>'+controls


STYLE = """
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f4f2eb;color:#183733;font:17px/1.55 system-ui,sans-serif}
main{max-width:860px;margin:auto;padding:24px clamp(14px,4vw,40px) 60px}header{padding:18px 0 24px}h1{font:700 clamp(32px,5vw,48px)/1.1 Georgia,serif;margin:12px 0}
h2{font:700 clamp(27px,4vw,38px)/1.15 Georgia,serif;margin:.3em 0}p{max-width:68ch}header p{margin:.6em 0 0}
.story,aside,.search{background:#fff;border:1px solid #d2d9d1;border-radius:14px;padding:clamp(15px,3vw,28px);margin:12px 0}
small{color:#496359}.story>small,header small,.chain>li>small,.outcome>small{font:bold 12px/1.5 system-ui;letter-spacing:.06em;text-transform:uppercase;display:block}
.chain{list-style:none;padding:0 0 0 20px;margin:22px 0}.chain>li{position:relative;border-left:3px solid #91afa1;padding:0 0 18px 20px}
.chain>li:before{content:"";position:absolute;left:-8px;top:3px;width:9px;height:9px;border:2px solid #346658;background:#fff;border-radius:50%}
.chain>.source:before{border-radius:2px;background:#ebc16a}.chain>li:last-child{border-color:transparent}.chain b{display:block}
.post>a,summary{font-size:.9em}.action a,button{display:inline-block;background:#18584a;color:white;border:0;border-radius:6px;padding:10px 16px;font-weight:650}
a{color:#175d50;text-underline-offset:.18em}summary,button{cursor:pointer}.outcome{padding:18px;background:#f1f6ed;border-left:4px solid #35755f;margin:16px 0}
.outcome h3{margin:.35em 0}.result{padding:10px 0;border-top:1px solid #dae0d8}form{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
label,input{display:block}input{max-width:100%;padding:8px}li,.result,p{overflow-wrap:anywhere}footer{font-size:.85em;color:#4e635a;margin:20px 0}
"""
