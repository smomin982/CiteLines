"""Replay only surviving page trials against the same January snapshot and pairs."""
import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from domains import page_site
from explorer import load_network


def run(db, folder):
    graph = load_network(db.resolve(), date(2025, 1, 31))
    counts, cache, examples = Counter(), {}, {}
    with (folder/"closures.csv").open(encoding="utf-8", newline="") as f, (
        folder/"site_closures.csv").open("w", encoding="utf-8", newline="") as out:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames + ["site","site_transfers","site_outcome"])
        writer.writeheader()
        for row in reader:
            if row["outcome"] == "disconnected":
                continue
            a,b,key = row["origin"],row["destination"],row["closed_page"]
            site = page_site(key)
            if (a,b,site) not in cache:
                path = graph.route(a,b,closed_site=site)
                cache[a,b,site] = len(path)//2 if path else None
            after = cache[a,b,site]
            before = int(row["backup_transfers"])
            assert after is None or after >= before
            outcome = "lost" if after is None else "longer" if after > before else "same_length"
            writer.writerow(dict(row, site=site, site_transfers=after, site_outcome=outcome))
            counts[outcome] += 1
            if outcome not in examples or int(row["original_transfers"]) < examples[outcome]["original"]:
                examples[outcome] = dict(a=a,b=b,page=key,original=int(row["original_transfers"]))
    result = dict(trials=sum(counts.values()), distinct_pair_site_tests=len(cache),
                  outcomes=dict(counts), examples=examples)
    (folder/"site_summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(result)


if __name__ == "__main__":
    run(Path(sys.argv[1]), Path(__file__).parent/"study")
