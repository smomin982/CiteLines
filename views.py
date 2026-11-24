"""Visitor-facing labels and views. Case captions describe notes, not unseen posts."""
from datetime import date, datetime, timezone
from hashlib import sha256
from html import escape
from urllib.parse import unquote, urlencode, urlsplit
from domains import page_site
from post_preview import card
from layout import case_header, step


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


def trial_id(page):
    return "trial-" + sha256(page.encode()).hexdigest()[:16]


def findings(summary, site_summary=None):
    n, trials = summary["pairs"], summary["trials"]
    fragile = summary["fragile_pairs"]
    body = ['<section class="story"><small>January 2025 · Closure study</small>'
            '<h2>How often does one source hold two posts together?</h2>',
            f'<p>We randomly selected {n:,} connected post pairs. For each pair we found a shortest '
            'citation chain, then removed and restored each page on that chain, one at a time.</p>',
            f'<article class="outcome"><h3>{fragile/n:.1%} of pairs depended on at least one page</h3>'
            f'<p>For {fragile:,} of {n:,} pairs, removing just one of their cited pages could eliminate '
            'every route between them in this network.</p></article>',
            f'<h3>What happened across {trials:,} individual removals?</h3>']
    for kind, label in (("unchanged","A route just as short survived"),
                        ("detour","Only a longer route survived"),
                        ("disconnected","No route survived")):
        count = summary["outcomes"].get(kind, 0)
        body.append(f'<article class="result"><b>{count/trials:.1%} · {label}</b>'
                    f'<div class="gauge {kind}" aria-hidden="true"><i style="width:{100*count/trials:.2f}%"></i></div>'
                    f'<p>{count:,} of {trials:,} page removals.')
        if ex := summary["examples"].get(kind):
            query = urlencode(dict(mode="stress", a=ex["a"], b=ex["b"], day="2025-01-31"))
            body.append(f' <a href="?{escape(query)}#{trial_id(ex["closed"])}">Inspect a real case →</a>')
        body.append("</p></article>")
    if site_summary:
        total = site_summary["trials"]
        body.append(f'<h3>Did the surviving backups need the same website?</h3><p>We retested only the {total:,} '
                    'page removals that left a backup. This time we removed every cited page on the same site.</p>')
        for kind,label in (("lost","No backup survived"),("longer","A longer backup survived"),
                           ("same_length","A backup of the same length survived")):
            count = site_summary["outcomes"].get(kind,0)
            body.append(f'<p><b>{count:,} ({count/total:.1%})</b> · {label}. ')
            if ex := site_summary["examples"].get(kind):
                body.append(link("Compare the three routes →",mode="compare",a=ex["a"],b=ex["b"],page=ex["page"]))
            body.append('</p>')
        body.append('<small>Lengths here are relative to the page-only backup, not the original route. '
                    'These are removal trials, not distinct pairs or sites.</small>')
    body.append('<details><summary>How to interpret these percentages</summary><p>Pairs were sampled '
                'uniformly without replacement from connected pairs, not from all X posts. Longer routes '
                'contribute more removal trials. Tied shortest routes use sorted neighbor order. Results '
                'measure shared URLs in this snapshot, not the independence or accuracy of the sources.</p>'
                '</details><p><a href="/">Explore a guided example →</a></p></section>')
    return "".join(body)


def note_excerpt(c):
    """Show a bounded, attributed excerpt from the witness, never inferred post text."""
    if not c.summary:
        return "<small>Note text unavailable in this database.</small>"
    text = " ".join(c.summary.split())
    excerpt = text if len(text) <= 280 else text[:279].rstrip() + "…"
    return f'<blockquote dir="auto">{escape(excerpt)}</blockquote>'


def chain(g, path, *, previews=True):
    if not path:
        return "<p>There is no chain of shared pages between these posts by this date.</p>"
    nodes = []
    for i, item in enumerate(path):
        if i % 2 == 0:
            role = "Starting post" if i == 0 else "Destination post" if i == len(path)-1 else "Connecting post"
            caption = CAPTIONS.get(item, "Post on X")
            nodes.append(f'<li class="post"><small>{role}</small><b>{escape(caption)}</b>'
                         +(card(item) if previews else
                           f'<a href="https://x.com/i/web/status/{escape(item)}" target="_blank" rel="noreferrer">Open post on X ↗</a>')
                         +'</li>')
        else:
            cites = [g.evidence[p, item] for p in (path[i-1], path[i+1])]
            proof = "".join(f"<li>Post {escape(c.post)} · note {escape(c.note)} · "
                            f"{datetime.fromtimestamp(c.millis/1000, timezone.utc):%d %b %Y} UTC"
                            f"<br>{escape(c.raw)}{note_excerpt(c)}</li>" for c in cites)
            nodes.append(f'<li class="source"><small>Both posts cite</small>'
                         f'<b><a href="{escape(item)}" target="_blank" rel="noreferrer">{escape(title(item))}</a></b>'
                         f'<details><summary>Inspect both citations</summary><ul>{proof}</ul></details></li>')
    return '<ol class="chain">' + "".join(nodes) + '</ol>'


def render_view(params, snapshot, cases, parse_id):
    base = next(iter(cases.values()))["before"]
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
    if mode == "compare":
        path = g.route(a, b)
        body = ('<small>Source dependence</small><h2>One page or the whole site?</h2>'
                '<p>Run two separate experiments on the same connection. First remove one cited page. '
                'Restore it, then remove every cited page on its site. The X posts themselves stay in place.</p>')
        if not path or len(path) < 3:
            body += '<p>No shared page to test for this pair at the selected cutoff.</p>'
        else:
            selected = params.get("page")
            if selected and a != b and (a,selected) in g.evidence and (b,selected) in g.evidence:
                path = [a,selected,b]
            pages = path[1::2]
            key = params.get("page", pages[0])
            if key not in pages:
                raise ValueError("Choose a cited page on the selected route.")
            domain = page_site(key)
            page_backup = g.route(a, b, key)
            site_backup = g.route(a, b, closed_site=domain)
            body += f'<p>Original route: <b>{len(path)//2} shared page(s)</b>. Testing <b>{escape(title(key))}</b>.</p>'
            for label, backup in (("Original connection", path),(f"Remove one page on {domain}", page_backup),
                                  (f"Remove all cited pages on {domain}", site_backup)):
                outcome = f"Connected via {len(backup)//2} shared page(s)" if backup else "Disconnected"
                body += f'<article class="outcome"><small>{escape(label)}</small><h3>{outcome}</h3>'
                body += f'<div class="strip"><b>Post …{escape(a[-6:])}</b> → '
                if backup:
                    body += ' → '.join(f'<span class="chip">{escape(title(p))}</span>' for p in backup[1::2])
                else:
                    body += '<em>No connecting pages</em>'
                body += f' → <b>Post …{escape(b[-6:])}</b></div>'
                if backup:
                    body += '<details><summary>Inspect route evidence</summary>'+chain(g, backup)+'</details>'
                body += '</article>'
            if page_backup and not site_backup:
                body += f'<p><b>The backup still depends on {escape(domain)}.</b> Removing one page left a way around it, but every surviving chain used at least one page on that site.</p>'
            elif site_backup:
                body += '<p>A route survives without any cited page on this site. Different sites do not necessarily provide independent evidence.</p>'
            else:
                body += '<p>The chosen page alone was already indispensable.</p>'
            body += f'<small>Site means registrable domain, including its subdomains. This is a URL grouping, not a publisher ownership check. Snapshot through {day} UTC.</small>'
            body += '<p>'+link("Try these removals on the interactive map →",mode="map",page=key,**common)+'</p>'
            if len(pages) > 1:
                body += '<h3>Try another page from this route</h3><ul>'+''.join(
                    '<li>'+link(title(k), mode="compare", page=k, **common)+'</li>' for k in pages if k != key)+'</ul>'
        body += '<p>'+link("Back to the original connection →", mode="route", **common)+'</p>'
    elif mode == "history":
        body = ('<small>Connection history</small><h2>When did a citation chain first exist?</h2>'
                f'<p>Looking at notes through {day:%d %B %Y}, UTC. A chain becomes possible once '
                'every citation along it has appeared in the archive.</p>')
        earliest = g.first_connected(a, b)
        if earliest is None:
            body += chain(g, None)
        else:
            stamp, old = earliest
            now = g.route(a, b)
            moment = datetime.fromtimestamp(stamp/1000, timezone.utc).isoformat(timespec="milliseconds")
            then_count, now_count = len(old)//2, len(now)//2
            body += (f'<article class="outcome"><small>First recorded connection (UTC)</small>'
                     f'<h3><time datetime="{moment}">{moment.replace("T"," ").removesuffix("+00:00")}</time></h3>'
                     f'<p>Shared pages needed then: <b>{then_count}</b>. By the selected date: <b>{now_count}</b>.</p></article>')
            if now_count < then_count:
                body += '<p>A shorter route appeared later. The shortcut alone would give the wrong first-connection date.</p>'
            body += '<h3>Shortest chain at that first instant</h3>' + chain(g, old)
            body += '<p>This dates the recorded citations, not when either author read or shared anything.</p>'
        body += link("View the route at the selected date →", mode="route", **common)
    elif mode == "nearby":
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
        heading = escape(cases[example]["heading"]) if example else "How are these posts connected?"
        intro = "Notes on both English-language posts cite this page."
        body = case_header(heading,example,day,path)
        body += step(1,"Read the original posts","posts")+'<div class="postpair">'+card(a,auto=True,label="Original post · A")
        if a != b:
            body += card(b,auto=True,label="Original post · B")
        body += '</div>'+step(2,"Follow the shared evidence","source")
        if path and len(path)==3:
            key = path[1]
            body += (f'<div class="shared"><small>Shared source</small><h3><a href="{escape(key)}" '
                     f'target="_blank" rel="noreferrer">{escape(title(key))}</a></h3><p>{intro}</p>'
                     '<details><summary>Read the two proposed Community Notes</summary>')
            for label,p in (("A",a),("B",b)):
                body += f'<small>Contributor note on post {label}</small>'+note_excerpt(g.evidence[p,key])
            body += '</details></div>'
        else:
            body += chain(g, path)
        if path and len(path) > 1 and mode != "stress":
            body += step(3,"Test the connection","experiment")
            text = "Remove that page and see what happens →" if len(path)==3 else "Try removing each shared page →"
            body += '<div class="action">'+link(text, mode="stress", **common)+'</div>'
        elif mode == "stress" and path:
            body += step(3,"What changed when the source was removed?","outcomes")
            if len(path) == 1:
                body += '<p>You selected the same post twice. There is no shared page to remove.</p>'
            for key, backup, delta in g.closures(path):
                label = "Disconnected" if delta is None else "Equal-length backup" if not delta else f"Detour: +{delta}"
                verdict = ("This page held the connection together." if delta is None else
                           "Another route is just as short." if not delta else "The connection survives, but takes a longer route.")
                detail = ("No chain remains in this snapshot." if backup is None else
                          f"The shortest chain now uses {len(backup)//2} shared pages instead of {len(path)//2}.")
                body += f'<article id="{trial_id(key)}" class="outcome"><small>{escape(label)} · single-page experiment</small><h3>{verdict}</h3><p>With <b>{escape(title(key))}</b> removed: {detail}</p>'
                if backup:
                    body += '<details open><summary>Follow the backup route</summary>'+chain(g, backup)+'</details>'
                body += '<p>'+link("Compare with removing the whole site →", mode="compare", page=key, **common)+'</p>'
                body += '</article>'
        tools = []
        if path and len(path) > 1:
            tools.append(link("Interactive route map →", mode="map", **common))
            tools.append(link("Page vs. whole site →", mode="compare", **common))
        tools += [link("Connection history →",mode="history",**common),
                  link("Nearby posts →",mode="nearby",**common)]
        body += '<div class="toolbox"><small>Keep exploring</small><div>'+"".join(tools)+'</div></div>'
    demos = "".join(link(c["heading"], a=c["before"][0], b=c["before"][-1])
                                   for c in cases.values())
    return '<section class="story">'+body+'</section><aside class="casepicker"><small>Case library</small><div>'+demos+'</div></aside>'+controls
