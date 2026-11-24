"""Offline topic index and queries for the immutable January note archive."""
import argparse
import re
import sqlite3
from pathlib import Path

from research.pilot import URL


def has_table(db, name):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                           (name,)).fetchone())


def index_topics(db):
    """Index note prose once; retain the note_text rowid for witness joins."""
    if not has_table(db, "note_text"):
        raise ValueError("This database has no note text. Rebuild it with route_map.py ingest.")
    if has_table(db, "topic_fts"):
        return
    db.execute("CREATE VIRTUAL TABLE topic_fts USING fts5(prose, tokenize='unicode61')")
    rows = db.execute("SELECT rowid,summary FROM note_text")
    db.executemany("INSERT INTO topic_fts(rowid,prose) VALUES(?,?)",
                   ((rowid, URL.sub(" ", summary)) for rowid,summary in rows))
    db.execute("CREATE INDEX IF NOT EXISTS citations_by_note ON citations(note,millis,page,post)")


def phrase(q):
    """Treat user input as a literal token phrase, not an FTS expression."""
    if len(q) > 160 or not re.search(r"[^\W_]", q):
        raise ValueError("Enter a word or phrase of up to 160 characters.")
    return '"' + q.replace('"','""') + '"'


MATCHES = """FROM topic_fts
             JOIN note_text n ON n.rowid=topic_fts.rowid
             JOIN citations c ON c.note=n.note
             WHERE topic_fts MATCH ? AND c.millis <= ?"""


def ranked_pages(db, q, cutoff, offset=0):
    """Return up to 21 rows (last row signals a next page), counting distinct posts."""
    return db.execute("SELECT c.page, COUNT(DISTINCT c.post) AS posts, MIN(n.rowid) "
                      + MATCHES + " GROUP BY c.page ORDER BY posts DESC,c.page LIMIT 21 OFFSET ?",
                      (phrase(q),cutoff,offset)).fetchall()


def topic_count(db, q, cutoff):
    """Eligible distinct posts, not notes, URLs or all-time totals."""
    return db.execute("SELECT COUNT(DISTINCT c.post) "+MATCHES,(phrase(q),cutoff)).fetchone()[0]


def matched_posts(db, q, cutoff, page):
    """One deterministic, matching witness per eligible post citing this page."""
    return db.execute("SELECT c.post, MIN(n.rowid) " + MATCHES +
                      " AND c.page=? GROUP BY c.post ORDER BY c.post",
                      (phrase(q),cutoff,page)).fetchall()


def excerpt(db, q, rowid):
    return db.execute("""SELECT n.note,snippet(topic_fts,0,'','',' … ',24)
                        FROM topic_fts JOIN note_text n ON n.rowid=topic_fts.rowid
                        WHERE topic_fts MATCH ? AND topic_fts.rowid=?""",
                      (phrase(q),rowid)).fetchone()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add topic search to a database with note text.")
    parser.add_argument("database", type=Path)
    path = parser.parse_args().database.resolve()
    with sqlite3.connect(path.as_uri()+"?mode=rw", uri=True) as db:
        db.execute("BEGIN")
        index_topics(db)
        print("Indexed notes:", db.execute("SELECT count(*) FROM topic_fts").fetchone()[0])
