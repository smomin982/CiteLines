# Community Notes Route Map

**One page or the whole site?** Open **A backup that still needs the same site** under the guided cases. Removing X's gambling advertising policy page leaves a six-page detour between these two posts, but excluding all `x.com` citations disconnects them. Every route offers the same comparison, with independent page and site trials.

**Connection history:** Choose **When did these posts first connect?** on a route, or open **A shortcut that appeared later** under the cases. The explorer compares the shortest chain at the first recorded connection with the chain at the selected cutoff.

**[January research findings](research/study/FINDINGS.md):** 485 of 500 sampled connected pairs depended on at least one cited page. Select **What we found** in the explorer to compare the 2,812 individual page removals and inspect real examples.

Trace the shortest citation chain between two X posts and close a page to see whether the connection survives. The [approved proposal](PROPOSAL.md) describes the project, and [SPEC.md](SPEC.md) defines the checkpoint behavior.

## Run the checkpoint (PowerShell, Python 3.11+)

**Browser interface:** With the database built, run `py -3 explorer.py january.sqlite` and open **http://127.0.0.1:8765/**. On the original development machine the existing database is available at `"$env:LOCALAPPDATA\Temp\opencode\checkpoint-jan.sqlite"`. The local server uses the Python standard library. Stop it with Ctrl+C.

Start with **Two posts, one Wikipedia article**. Follow the chain, then click **Remove that page and see what happens** to reveal the backup route. The sultan’s portrait case shows the opposite outcome. To discover other destinations, click **Explore other posts connected to the starting post**. The search panel accepts post IDs or URLs and an end-of-day UTC cutoff. Each page-removal trial affects just one page and one post pair.

Download the five archives using the `$files` block in [research/README.md](research/README.md). From the repository root:

```powershell
py -3 route_map.py ingest january.sqlite @files
py -3 route_map.py route january.sqlite 1882827830331085172 1884646064566796739
py -3 route_map.py route january.sqlite 1882827830331085172 1884646064566796739 --close https://de.m.wikipedia.org/wiki/Demokratie
```

The example goes from one transfer to two. Each result includes the supporting note IDs. Use `--cutoff 2025-01-28T23:59:59Z` to ask the same question before the second endpoint's citations existed. To run tests, install `pytest` in your Python environment, then run `python -m pytest -q` from this directory.

## Checkpoint status

The instructor approved the topic change. January ingestion, shortest routes, evidence lookup, cutoff filtering, and single-page closures work from the CLI. The five archives produced 144,219 distinct citation records; the CLI reproduced both verified pilot cases, and four pytest tests pass. Scope remains January 2025. The neighborhood explorer, Streamlit views, scaling measurements, and closure-frequency analysis remain for the final submission.
