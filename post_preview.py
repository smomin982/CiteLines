"""Live, text-only public X previews; never substitute Community Notes for post text."""
import json
import re
from functools import lru_cache
from html import escape
from html.parser import HTMLParser
from time import monotonic
from urllib.parse import urlencode
from urllib.request import urlopen


class EmbedText(HTMLParser):
    """Only read text in the provider's post paragraph, not its attribution or HTML."""
    def __init__(self):
        super().__init__()
        self.inside = False
        self.parts = []
        self.date = ""
        self.language = ""

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.inside = True
            self.language = (dict(attrs).get("lang") or "").lower()
        elif tag == "br" and self.inside:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "p":
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)
        elif re.fullmatch(r"[A-Za-z]+ \d{1,2}, \d{4}", data.strip()):
            self.date = data.strip()


@lru_cache(maxsize=256)
def fetch_preview(post, cache_interval):
    query = urlencode(dict(url="https://twitter.com/i/status/"+post, omit_script="true", dnt="true"))
    with urlopen("https://publish.twitter.com/oembed?"+query, timeout=4) as resp:
        doc = json.load(resp)
    parser = EmbedText()
    parser.feed(doc["html"])
    text = "".join(parser.parts).strip()
    if not text:
        raise ValueError("No public text")
    return dict(author=doc["author_name"], text=text, date=parser.date, language=parser.language)


def preview(post):
    if not re.fullmatch(r"[0-9]{1,20}", post):
        raise ValueError("Invalid post ID")
    return fetch_preview(post, int(monotonic()//300))


def card(post, *, auto=False, label="Original X post"):
    ident = escape(post)
    return (f'<article class="xcard" data-post="{ident}" data-auto="{int(auto)}"><small>{escape(label)}</small>'
            '<div class="xcontent" aria-live="polite"></div>'
            '<button class="xload" type="button" hidden>Show original post</button> '
            f'<a href="https://x.com/i/web/status/{ident}" target="_blank" rel="noreferrer">Open on X ↗</a></article>')


SCRIPT = """<script>
for (const card of document.querySelectorAll('.xcard')) {
 const button=card.querySelector('button'), box=card.querySelector('.xcontent');
 button.hidden=false;
 const load=async()=>{
   button.hidden=true; box.textContent='Loading original post…';
   try {
     const response=await fetch('/post-preview?id='+encodeURIComponent(card.dataset.post));
     if (!response.ok) throw Error();
     const item=await response.json(), author=document.createElement('strong'),
       text=document.createElement('p'), date=document.createElement('small');
     author.textContent=item.author; text.dir='auto'; text.textContent=item.text;
     date.textContent=item.date; box.replaceChildren(author,text,date);
   } catch {
     box.textContent='Original post unavailable here. You can still inspect the archived note and its citation.';
     button.textContent='Retry'; button.hidden=false;
   }
 };
 button.onclick=load;
 if(card.dataset.auto==='1') load();
}
</script>"""
