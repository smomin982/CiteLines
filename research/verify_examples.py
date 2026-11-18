"""Recheck selected examples against raw January rows, without the route finder."""
import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

from pilot import END, START, URL, page


def verify(report, archives):
    cases = report["cases"]
    assert set(cases) == {"disconnected", "detour"}
    wanted = {w["post"] for c in cases.values() for w in c["witnesses"]}
    source_pages = defaultdict(set)
    source_records = set()
    for path in archives:
        with zipfile.ZipFile(path) as archive, archive.open(archive.namelist()[0]) as f:
            rows = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"), delimiter="\t",
                                  quoting=csv.QUOTE_NONE)
            for r in rows:
                if r["tweetId"] not in wanted or not START <= int(r["createdAtMillis"]) < END:
                    continue
                for match in URL.findall(r["summary"]):
                    text = match.rstrip(".,;!?")
                    while text.endswith(")") and text.count(")") > text.count("("):
                        text = text[:-1]
                    key = page(text)
                    if key:
                        source_records.add((r["tweetId"], r["noteId"], text, key))
                        source_pages[r["tweetId"]].add(key)

    for kind, c in cases.items():
        for w in c["witnesses"]:
            assert (w["post"], w["note"], w["raw"], w["page"]) in source_records
        a, closed, b = c["before"]
        assert closed == c["removed"]
        assert closed in source_pages[a] & source_pages[b]
        remaining = [source_pages[p] - {closed} for p in (a, b)]
        if kind == "disconnected":
            assert not all(remaining), "Expected one isolated endpoint"
        else:
            assert not remaining[0] & remaining[1], "A one-transfer route survived"
            alt = c["after"]
            assert alt[0] == a and alt[-1] == b and closed not in alt
            for post, key in zip(alt[::2], alt[1::2]):
                assert key in source_pages[post]
            for key, post in zip(alt[1::2], alt[2::2]):
                assert key in source_pages[post]
        print(kind, "verified from raw rows")


if __name__ == "__main__":
    verify(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), sys.argv[2:])
