"""A topic-first way to choose real posts for the existing route experiments."""
from datetime import date, datetime, time, timezone
from html import escape

from topic_search import excerpt, has_table, matched_posts, ranked_pages
from views import link, title


def topic_view(db, params):
    day = date.fromisoformat(params.get("day","2025-01-31"))
    if not date(2025,1,1) <= day <= date(2025,1,31):
        raise ValueError("Select a date in January 2025.")
    cutoff = int(datetime.combine(day,time(23,59,59),timezone.utc).timestamp())*1000+999
    q = params.get("q","").strip()
    common = dict(mode="topics",day=str(day))
    body = ['<section class="story"><small>Topic explorer</small><h2>What sources do people cite on this topic?</h2>'
            '<p>Search notes by word or exact phrase. Counts include only posts with a matching note '
            'that cites that page. Website addresses are excluded from the text search.</p>'
            '<form><input type="hidden" name="mode" value="topics"><label>Word or phrase'
            f'<input name="q" required maxlength="160" placeholder="gambling" value="{escape(q)}"></label>'
            f'<label>Through date (UTC)<input type="date" name="day" value="{day}" min="2025-01-01" max="2025-01-31"></label>'
            '<button>Search notes</button></form><p>Try: ' +
            ' · '.join(link(s,q=s,**common) for s in ("gambling","wildfire","democracy")) + '</p></section>']
    if not has_table(db,"topic_fts"):
        return "".join(body)+'<p>Topic index unavailable. See the README for database setup.</p>'
    if not q:
        return "".join(body)
    offset = max(0,int(params.get("offset","0")))
    common["q"] = q
    body.append('<section class="story">')
    key = params.get("page")
    def witness(rowid):
        note,text = excerpt(db,q,rowid)
        return f'<blockquote dir="auto">{escape(text)}</blockquote><small>Matching proposed note {escape(note)}</small>'
    if not key:
        rows = ranked_pages(db,q,cutoff,offset)
        body.append(f'<h3>Pages cited in notes matching “{escape(q)}”</h3>')
        if not rows:
            body.append('<p>No pages found here. Try a shorter phrase or a later cutoff.</p>')
        for key_id,count,rowid in rows[:20]:
            body.append('<article class="result">'+link(title(key_id),page=key_id,**common)+
                        f'<p><b>{count:,}</b> matching post{"s" if count != 1 else ""} · {escape(key_id)}</p>'+
                        witness(rowid)+'</article>')
        more = len(rows)>20
    else:
        body.append('<p>'+link("← Back to matching sources",**common)+'</p>')
        common["page"] = key
        rows = matched_posts(db,q,cutoff,key)
        body.append(f'<h3>{escape(title(key))}</h3><p>{len(rows):,} matching posts cite {escape(key)}.</p>')
        first = params.get("first")
        if first:
            first_row = dict(rows).get(first)
            if first_row is None:
                raise ValueError("The starting post must match this topic, page and cutoff.")
            body.append('<article class="outcome"><small>First post selected</small>'+witness(first_row)+
                        '<p>'+link("Choose a different first post",**common)+'</p></article>')
            common["first"] = first
        elif len(rows)>1:
            body.append('<p>Choose a first post, then another to compare. The experiments use the '
                        'full citation network at this date, including notes outside this topic.</p>')
        for post,rowid in rows[offset:offset+20]:
            body.append('<article class="result">'+witness(rowid)+f'<p>Post {escape(post)} · ')
            if not first and len(rows)>1:
                body.append(link("Start with this post",first=post,offset=offset,**common))
            elif first and post != first:
                pair = dict(mode="source_pair",a=first,b=post,page=key,day=str(day))
                body.append(' · '.join(link(label,action=action,**pair) for label,action in
                                       (("Compare page vs. site","compare"),("View route","route"),
                                        ("Connection history","history"))))
            else:
                body.append(link("Explore from this post",mode="nearby",a=post,day=str(day)))
            body.append('</p></article>')
        more = len(rows)>offset+20
    if offset:
        body.append(link("← Previous",offset=max(0,offset-20),**common))
    if more:
        body.append(link("Next 20 →",offset=offset+20,**common))
    return "".join(body)+'</section>'
