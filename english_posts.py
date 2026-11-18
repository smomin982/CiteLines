"""Build and apply an original-post language allowlist. Source pages are not labels."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
from urllib.error import HTTPError

from post_preview import preview

MANIFEST = Path(__file__).resolve().parent / "data/english_posts.json"


def english(tag):
    return tag.lower().split("-")[0] == "en"


def collection():
    return frozenset(p for p,tag in json.loads(MANIFEST.read_text()).items() if english(tag))


def scope(db, ids):
    """Shadow the immutable archive with a connection-local English citation view."""
    db.execute("CREATE TEMP TABLE english_ids(id TEXT PRIMARY KEY)")
    db.executemany("INSERT INTO english_ids VALUES(?)", ((p,) for p in ids))
    db.execute("CREATE TEMP VIEW citations AS SELECT c.* FROM main.citations c "
               "JOIN english_ids e ON e.id=c.post")


def verified(db, limit):
    # Deliberately sample several shared-source neighborhoods for a usable walkthrough.
    # English-looking page URLs select candidates only; each original still needs verification.
    ids = {}
    for pattern in ("%nasa.gov%", "%newsweek.com%wildfire%", "%bbc.co.uk%", "%wikipedia.org%",
                    "%business.x.com%", "%reuters.com%"):
        pages = db.execute("SELECT page FROM citations WHERE page LIKE ? GROUP BY page "
                           "HAVING COUNT(DISTINCT post)>1 ORDER BY COUNT(DISTINCT post) DESC,page LIMIT 8",
                           (pattern,))
        for (page,) in pages:
            ids.update(db.execute("SELECT DISTINCT post,1 FROM citations WHERE page=? ORDER BY post LIMIT 8",
                                  (page,)))
    def check(p):
        try:
            return p,preview(p)["language"]
        except HTTPError as exc:
            if exc.code == 429:
                raise
        except (OSError,ValueError,KeyError):
            pass
        return p,""
    with ThreadPoolExecutor(max_workers=4) as pool:
        return {p:lang for p,lang in pool.map(check,list(ids)[:limit]) if english(lang)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database",type=Path)
    parser.add_argument("--limit",type=int,default=350)
    parser.add_argument("--out",type=Path,default=MANIFEST)
    args = parser.parse_args()
    with sqlite3.connect(args.database.resolve().as_uri()+"?mode=ro",uri=True) as db:
        labels = verified(db,args.limit)
    if not labels:
        raise SystemExit("No English originals verified; not replacing manifest")
    args.out.write_text(json.dumps(labels,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"{len(labels)} verified English originals")
