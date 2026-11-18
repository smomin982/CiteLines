"""Search the local citation index; never fetch the user-supplied URL."""
from html import escape
from urllib.parse import urlsplit

from domains import page_site
from research.pilot import page
from views import CAPTIONS, link, note_excerpt, title
from post_preview import card


def source_view(graph, params, day):
    q = params.get("q", "").strip()
    base = dict(mode="sources", day=str(day))
    form = (f'<section class="story"><small>Source explorer</small><h2>Which posts cite this source?</h2>'
            '<p>Enter a domain to browse its pages, or paste a full article URL to see the posts that cite it.</p>'
            f'<form><input type="hidden" name="mode" value="sources"><label>Domain or article URL'
            f'<input name="q" value="{escape(q)}" placeholder="bbc.co.uk"></label><label>Through date (UTC)'
            f'<input type="date" name="day" min="2025-01-01" max="2025-01-31" value="{day}"></label>'
            '<button>Find citations</button></form><p>Try: ' +
            ' · '.join(link(s, q=s, **base) for s in ("wikipedia.org","bbc.co.uk","x.com")) +
            '</p></section>')
    if not q:
        return form
    exact = "://" in q or "/" in q.rstrip("/")
    raw = q if "://" in q else "https://" + q
    if urlsplit(raw).scheme.lower() not in {"http","https"} or not (key := page(raw)):
        return form+"<section class='story'>Enter a domain or an HTTP(S) page URL indexed by the study.</section>"
    offset = max(0,int(params.get("offset","0")))
    body = ['<section class="story">']
    if exact:
        posts = graph.adj.get(key, ())
        body.append(f'<h3>{escape(title(key))}</h3><p>{escape(key)}</p>'
                    f'<p><b>{len(posts):,} distinct citing posts</b> through {day}.</p>')
        if len(posts) >= 2:
            body.append('<p>Read what the contributors wrote, then choose two posts to compare. '
                        'These are proposed notes, not the original posts.</p>')
        first = params.get("first")
        if first:
            if (first,key) not in graph.evidence:
                raise ValueError("The starting post does not cite this page by that date.")
            base["first"] = first
            body.append(f'<article class="outcome"><small>Selected first post</small>'
                        +card(first,auto=True)+note_excerpt(graph.evidence[first,key])+
                        link("Choose a different starting post",mode="sources",day=str(day),q=q,offset=offset)+'</article>')
        for p in posts[offset:offset+20]:
            c = graph.evidence[p,key]
            body.append('<div class="result">'+link(CAPTIONS.get(p, "Post "+p),mode="nearby",a=p,day=str(day))+
                        card(p)+f'<small>Proposed note {escape(c.note)}</small>'+note_excerpt(c))
            if not first and len(posts) >= 2:
                body.append(link("Start with this post",q=q,offset=offset,first=p,**base))
            elif first and first != p:
                pair = dict(mode="source_pair", page=key, day=str(day), a=first, b=p)
                body.append(" · ".join(link(label,action=action,**pair) for label,action in
                                       (("Compare page vs. site","compare"),("View route","route"),
                                        ("See connection history","history"))))
            body.append("</div>")
        size = len(posts)
        if not size:
            body.append('<p>No match for this page key. Try the bare domain to browse other URL variants.</p>')
    else:
        site = page_site(key)
        pages = sorted(graph.pages_by_site.get(site,()), key=lambda k:(-len(graph.adj[k]),k))
        size = len(pages)
        body.append(f'<h3>{escape(site)} · {size:,} cited pages</h3>'
                    '<p>Ranked by distinct posts citing each page, not by how important it is to a route.</p>')
        for k in pages[offset:offset+20]:
            body.append('<div class="result">'+link(title(k), q=k, **base)+
                        f'<br><small>{len(graph.adj[k]):,} citing posts · {escape(k)}</small></div>')
    if offset:
        body.append(link("← Previous",q=q,offset=max(0,offset-20),**base))
    if offset+20 < size:
        body.append(link("Next 20 →",q=q,offset=offset+20,**base))
    return form+"".join(body)+"</section>"
