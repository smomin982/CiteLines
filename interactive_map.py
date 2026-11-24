"""Server-computed route states with an in-place, keyboard-accessible browser view."""
from html import escape

from domains import page_site
from post_preview import card
from views import chain, link, note_excerpt, title


CASES = (
    ("detour", "Find a backup route", "Federal funding freeze",
     "1884244793590698460", "1884304755348091251"),
    ("broken", "Break a connection", "California wildfires",
     "1877780688864170019", "1879699663114441182"),
    ("site", "Find a backup that needs the same site", "Romanian elections",
     "1879130375278211292", "1879574269140615626"),
    ("history", "Find a shortcut that appeared later", "Federal benefits",
     "1884304755348091251", "1884342140848800071"),
)


def examples(graph):
    """Offer only examples whose advertised outcome still holds in this graph."""
    cards = []
    for kind, label, topic, a, b in CASES:
        route = graph.route(a,b)
        if not route or len(route)<3:
            continue
        key = route[1]
        after = graph.route(a,b,key) if kind!="history" else None
        if kind == "detour":
            valid = after and len(after)>len(route)
        elif kind == "broken":
            valid = after is None
        elif kind == "site":
            valid = after and not graph.route(a,b,closed_site=page_site(key))
        else:
            first = graph.first_connected(a,b)
            valid = first and len(first[1])>len(route)
        if valid:
            mode = "history" if kind=="history" else "map"
            cards.append('<article><small>'+escape(topic)+'</small>'+
                         link(label,mode=mode,a=a,b=b,day="2025-01-31")+'</article>')
    return ('<section class="story case-browser"><small>Case library · January 2025</small>'
            '<h2>Pick an outcome to explore</h2><div class="case-grid">'+"".join(cards)+
            '</div></section>') if cards else ""


def route_strip(path, original, selected=None, *, compact=False):
    if path is None:
        return '<div class="route-track broken"><b>Post A</b><span>No surviving citation chain</span><b>Post B</b></div>'
    nodes = ['<div class="route-track"><b>Post A</b>']
    for i,key in enumerate(path[1::2]):
        name = title(key)
        if compact:
            domain = page_site(key)
            name = {"reuters.com":"Reuters","apnews.com":"AP News","kiplinger.com":"Kiplinger"}.get(domain,domain)
        if i:
            nodes.append('<span class="via-post">Connecting post</span>')
        if selected is not None:
            nodes.append(f'<button class="map-source" type="button" data-map-node="{i}" '
                         f'aria-pressed="{str(i==selected).lower()}">{escape(title(key))}</button>')
        else:
            state, tag = ("retained","") if key in original else ("added","<small>New · </small>")
            nodes.append(f'<span class="map-source {state}" title="{escape(title(key))}">{tag}{escape(name)}</span>')
    nodes.extend(['<b>Post B</b>', '</div>'])
    return "".join(nodes)


def map_view(graph, a, b, day, library, default_page=None):
    route = graph.route(a,b)
    options = dict(a=a,b=b,day=str(day))
    example = next((case[2] for case in CASES if (a,b)==case[3:5]), None)
    badge = f"CASE FILE / {example}" if example else "SOURCE EXPERIMENT"
    intro = ('Community Notes are written by contributors to add context to posts on X. '
             'CiteLines follows the sources they cite to see what connects two posts.')
    body = (f'<section class="story experiment"><div class="lab-hero"><div><small>{escape(badge)}</small>'
            '<h1>Take away a source.<br><em>See what still connects.</em></h1>'
            f'<p>{intro}</p></div><div class="lab-key"><small>HOW TO READ THE MAP</small>'
            '<div><b>A</b><span></span><i>Source</i><span></span><b>B</b></div>'
            '<p>Post A and Post B are linked when a Community Note on each cites the same page.</p></div></div>')
    if not route or len(route)<3:
        return (body+'<p>No citation chain between two distinct posts at this cutoff.</p><p>'+
                link("Edit the posts or cutoff →",mode="route",**options)+'</p></section>'+library)
    sources = route[1::2]
    if default_page in sources:
        i = sources.index(default_page)
    elif default_page and (a,default_page) in graph.evidence and (b,default_page) in graph.evidence:
        route, sources, i = [a,default_page,b], [default_page], 0
    else:
        i = 0
    body += ('<div data-route-map><div class="lab-heading"><div><small>01 / ONE-CLICK DEMO</small>'
             '<h2>Can these posts stay connected?</h2></div>'
             f'<small>NOTES THROUGH {day:%d %b %Y} UTC</small></div>')
    if len(sources)==1:
        domain = page_site(sources[0])
        host = "Reuters" if domain=="reuters.com" else escape(domain)
        body += (f'<p>Both posts have a note citing the same <strong>{host} page</strong>. '
                 'Is that page the only link between them?</p>')
    else:
        body += '<p>The posts connect through a chain of cited pages. Pick a page to test.</p>'
    body += ('<div class="map-picks source-picker" role="group" aria-label="Source to inspect"'
             +(' hidden' if len(sources)==1 else '')+'>')
    for n,key in enumerate(sources):
        body += f'<button type="button" data-source="{n}" aria-pressed="{str(n==i).lower()}">{escape(title(key))}</button>'
    body += '</div>'
    def result(key,state,path):
        site = page_site(key)
        what = {"original":"No sources removed", "page":f"Removed page: {title(key)}",
                "site":f"Removed every cited page on {site}"}[state]
        count = len(path)//2 if path else 0
        status = (f'{count} shared {"page" if count==1 else "pages"}' if path else "Disconnected")
        if state=="original":
            headline = "The starting connection"
            explanation = ""
        elif not path:
            headline = "The connection breaks"
            explanation = "The remaining notes do not provide a chain of shared sources between these posts."
        elif count > len(route)//2:
            headline = "The connection survives, with a detour"
            middle = "one other post" if count==2 else f"{count-1} other posts"
            explanation = f"The same two posts are now linked through {count} cited pages and {middle}."
        else:
            headline = "Another route is just as short"
            explanation = "Other cited pages can still connect these posts in the same number of steps."
        view = route_strip(path,set(sources),sources.index(key) if state=="original" else None,
                           compact=state!="original")
        if state!="original":
            initial = len(route)//2
            unit = "page" if initial==1 else "pages"
            view = (f'<div class="demo-compare"><section class="demo-before"><small>Before · No removals</small>'
                    f'<h4>{initial} shared {unit}</h4>{route_strip(route,set(sources),compact=True)}</section>'
                    f'<section class="demo-after"><small>After · {"Page removed" if state=="page" else "Site removed"}</small>'
                    f'<h4>{status}</h4>{view}</section></div>')
        return (f'<div class="lab-verdict {escape(state)}"><div><small>{escape(what)}</small>'
                f'<h3>{headline}</h3></div>'+ (f'<strong>{status}</strong>' if state=="original" else "")+'</div>'
                +(f'<p class="verdict-copy">{explanation}</p>' if explanation else "")+view+
                ('<details><summary>Inspect the citations on this route</summary>'+chain(graph,path,previews=False)+'</details>' if path else ""))
    def evidence(key):
        j = route.index(key)
        notes = [(route[j-1],graph.evidence[route[j-1],key]),(route[j+1],graph.evidence[route[j+1],key])]
        return (f'<h3>Why this source connects the posts</h3><p><a href="{escape(key)}" rel="noreferrer" '
                f'target="_blank">{escape(title(key))} ↗</a></p><div class="postpair">'+ "".join(
                    f'<div><small>Proposed note {escape(c.note)} · post …{escape(p[-6:])}</small>{note_excerpt(c)}</div>'
                    for p,c in notes)+'</div>')
    action = "Remove this page" if len(sources)==1 else "Remove selected page"
    body += ('<div class="map-picks lab-actions" role="group" aria-label="Route experiment">'
             f'<button type="button" data-state="page" aria-pressed="false">{action} <span aria-hidden="true">→</span></button>'
             '<button type="button" data-state="original" aria-pressed="true" hidden>Reset demo</button></div>'
             '<p class="lab-help">This only changes the map. It doesn’t remove anything from X.</p>')
    body += '<div class="map-result" data-map-result aria-live="polite">'+result(sources[i],"original",route)+'</div>'
    body += ('<details class="map-notes demo-followup"><summary>Want to go further? Try removing the whole site</summary>'
             '<p>This removes all citations from the selected website instead of just one page.</p>'
             '<button type="button" data-state="site" aria-pressed="false">Remove the whole site</button></details>')
    body += '<details class="map-notes" data-map-notes><summary>Read the two notes that cite this source</summary><div>'+evidence(sources[i])+'</div></details>'
    for n,key in enumerate(sources):
        paths = (("original",route),("page",graph.route(a,b,key)),
                 ("site",graph.route(a,b,closed_site=page_site(key))))
        for state,path in paths:
            body += f'<template data-result="{n}-{state}">'+result(key,state,path)+'</template>'
        body += f'<template data-notes="{n}">'+evidence(key)+'</template>'
    body += ('<noscript><p>Use the '+link("static page/site comparison",mode="compare",page=sources[i],**options)+
             ' if JavaScript is off.</p></noscript></div><div class="lab-heading lab-posts"><div><small>02 / CHECK THE EVIDENCE</small>'
             '<h2>The original posts</h2></div></div><p>These are the authors’ posts on X, not the notes written about them.</p><div class="postpair">'
             +card(a,auto=True,label="Original post · A")+card(b,auto=True,label="Original post · B")+'</div>')
    body += '<p class="lab-links">'+link("See when these posts first connected →",mode="history",**options)+' · '+link("Look up a different pair →",mode="route",**options)+'</p></section>'
    return body+library


SCRIPT = """<script>
for (const map of document.querySelectorAll('[data-route-map]')) {
  const source = [...map.querySelectorAll('button[data-source]')];
  const states = [...map.querySelectorAll('button[data-state]')];
  let selected = source.find(btn => btn.getAttribute('aria-pressed')==='true').dataset.source;
  let state = 'original';
  const copy = (selector) => map.querySelector(selector).content.cloneNode(true);
  function update(updateNotes) {
    for (const btn of source) btn.setAttribute('aria-pressed', btn.dataset.source===selected);
    for (const btn of states) btn.setAttribute('aria-pressed', btn.dataset.state===state);
    map.querySelector('[data-state=original]').hidden = state==='original';
    map.querySelector('[data-map-result]').replaceChildren(copy(`[data-result="${selected}-${state}"]`));
    if (updateNotes) {
      const notes = map.querySelector('[data-map-notes]');
      notes.querySelector('div').replaceChildren(copy(`[data-notes="${selected}"]`));
      notes.open = true;
    }
  }
  for (const btn of source) btn.addEventListener('click',()=>{selected=btn.dataset.source;update(true);});
  for (const btn of states) btn.addEventListener('click',()=>{
    state=btn.dataset.state; update(false);
    const result=map.querySelector('[data-map-result]');
    if (state==='original') map.querySelector('[data-state=page]').focus();
    if (result.getBoundingClientRect().top+115>window.innerHeight || state==='site')
      result.scrollIntoView({block:'start'});
  });
  map.querySelector('[data-map-result]').addEventListener('click',e=>{
    const node=e.target.closest('[data-map-node]');
    if (!node) return;
    selected=node.dataset.mapNode; update(true);
    map.querySelector(`[data-map-node="${selected}"]`).focus();
  });
}
</script>"""
