"""Audit regressions: archive boundaries, URL identity and dated route witnesses."""
import sqlite3
from zipfile import ZipFile

from route_map import START, END, Citation, CitationNetwork, build


def test_data_contract_from_tsv_to_database(tmp_path):
    header = "tweetId\tnoteId\tcreatedAtMillis\tsummary\n"
    raw = "https://EXAMPLE.org/watch?v=A&utm_campaign=one#section"
    other = "https://example.org/watch?v=B"
    lines = [(10,1,START-1,other), (10,2,START,f"{raw} {raw}"),
             (20,3,END-1,f"{other} https://t.co/unknown"), (30,4,END,other)]
    archive = tmp_path/"part.zip"
    with ZipFile(archive, "w") as z:
        z.writestr("part.tsv", header+"".join("\t".join(map(str,r))+"\n" for r in lines))
    with sqlite3.connect(":memory:") as db:
        build(db,[archive])
        assert db.execute("SELECT count(*) FROM note_text").fetchone()[0] == 2
        assert db.execute("SELECT summary FROM note_text WHERE note='2'").fetchone()[0] == f"{raw} {raw}"
        assert db.execute("SELECT post,page,note,raw,millis FROM citations ORDER BY post").fetchall() == [
            ("10","https://example.org/watch?v=A","2",raw,START),
            ("20",other,"3",other,END-1)]


def test_first_connected_matches_rebuilt_snapshots_including_ties_and_duplicates():
    rows = [("1","p",30), ("2","p",30), ("1","q",20), ("3","q",5),
            ("3","r",10), ("2","r",10), ("1","q",8), ("4","isolated",1)]
    records = [Citation(a,k,str(i),k,t) for i,(a,k,t) in enumerate(rows)]
    full = CitationNetwork(records, 30)
    assert full.route("1","2") == ["1","p","2"]
    assert full.first_connected("1","2") == (10, ["1","q","3","r","2"])
    assert full.first_connected("1","1") == (8, ["1"])
    assert full.first_connected("1","4") is None
    assert full.first_connected("999","999") is None
    # Reference: rebuild the ordinary BFS graph at every distinct event instant.
    for a in "1234":
        for b in "1234":
            expected = None
            for t in sorted({r.millis for r in records}):
                p = CitationNetwork(records,t).route(a,b)
                if p:
                    expected = (t,p)
                    break
            assert full.first_connected(a,b) == expected
