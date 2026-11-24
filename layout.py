"""Shared application frame and a navigable map of a direct citation connection."""
from html import escape
from pathlib import Path
from urllib.parse import urlsplit


STYLE = (Path(__file__).parent/"atlas.css").read_text(encoding="utf-8")


def frame(content, mode, script, count):
    tabs = [("route","/","Try it"),("topics","?mode=topics","Topics"),
            ("sources","?mode=sources","Sources"),("findings","?mode=findings","Findings")]
    active = mode if mode in {"topics","sources","findings"} else "route"
    links = "".join(f'<a href="{url}"'+(' aria-current="page"' if k==active else '')+
                    f'>{name}</a>' for k,url,name in tabs)
    label = next(name for k,_,name in tabs if k==active)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><title>{label} · CiteLines</title><style>{STYLE}</style></head>'
            '<body><a class="skip" href="#content">Skip to content</a><header class="mast"><div class="mast-inner">'
            '<a class="brand" href="/" aria-label="CiteLines home"><span class="brandmark" aria-hidden="true">⌁</span>CiteLines</a>'
            f'<nav aria-label="Main">{links}</nav></div></header><main id="content">'
            '<div class="edition"><span>CITATION ATLAS <i>/</i> JAN 2025</span>'
            f'<span>{count} verified English posts</span></div>{content}'
            '<footer><b>CiteLines</b><span>Community Notes archive · January 2025<br>'
            'A shared source is a connection, not proof of agreement.</span></footer></main>'
            f'{script}</body></html>')


def case_header(heading, example, day, path):
    direct = path and len(path)==3
    text = ('Two people posted on X. Contributors added context to each post, citing the same page. '
            'Follow the evidence, then try removing that page.' if direct else
            'Trace the pages cited in Community Notes to see how these posts connect in the archive.')
    diagram = ""
    if direct:
        host = escape(urlsplit(path[1]).hostname or "Shared page")
        diagram = (f'<figure class="map"><figcaption>FIG. 01 <span>SHARED CITATION</span></figcaption>'
                   '<div class="rail"><a class="station" href="#posts"><i>A</i>Post A</a>'
                   f'<a class="station sourcepin" href="#source"><i>↗</i>{host}</a>'
                   '<a class="station" href="#posts"><i>B</i>Post B</a></div>'
                   '<p>Both notes cite the middle page.</p></figure>')
    return (f'<div class="casehead"><div><small>{"FIELD GUIDE" if example else "ROUTE EXPLORER"}'
            f' &nbsp;/&nbsp; {day:%d %b %Y}</small><h1>{heading}</h1><p>{text}</p></div>{diagram}</div>')


def step(number, title, anchor):
    return f'<h3 class="step" id="{anchor}"><span>{number:02}</span>{title}</h3>'
