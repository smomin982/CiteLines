"""Add verified English originals across topic neighborhoods; retain existing IDs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random
import sqlite3
from urllib.error import HTTPError

from english_posts import MANIFEST, english
from post_preview import preview
from topic_catalog import GROUPS
from topic_search import MATCHES, phrase


def expand(db, manifest, per_term):
    labels = json.loads(manifest.read_text())
    candidates = set()
    rng = random.Random(507)
    for terms in GROUPS.values():
        for term in terms:
            rows = db.execute("SELECT c.post, MIN(c.millis) "+MATCHES+
                              " GROUP BY c.post ORDER BY MIN(c.millis),c.post",
                              (phrase(term),1738367999999))
            posts = [p for p,_ in rows if p not in labels]
            # Include early posts for visitors choosing a narrow cutoff as well.
            early = min(4,per_term,len(posts))
            candidates.update(posts[:early])
            candidates.update(rng.sample(posts[early:],min(per_term-early,len(posts)-early)))
    def check(post):
        try:
            tag=preview(post)["language"]
            return post,tag if english(tag) else ""
        except HTTPError as exc:
            if exc.code == 429:
                raise
        except (OSError,ValueError,KeyError):
            pass
        return post,""
    with ThreadPoolExecutor(max_workers=4) as pool:
        for post,tag in pool.map(check,sorted(candidates)):
            if tag:
                labels[post]=tag
    manifest.write_text(json.dumps(labels,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"Checked {len(candidates)} candidates; collection now has {len(labels)} posts.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database",type=Path)
    parser.add_argument("--per-term",type=int,default=16)
    args=parser.parse_args()
    with sqlite3.connect(args.database.resolve().as_uri()+"?mode=ro",uri=True) as conn:
        expand(conn,MANIFEST,args.per_term)
