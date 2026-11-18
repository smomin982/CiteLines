# Community Notes Route Map

Trace the shortest citation chain between two X posts and close a page to see whether the connection survives. The [approved proposal](PROPOSAL.md) describes the project, and [SPEC.md](SPEC.md) defines the checkpoint behavior.

## Run the checkpoint (PowerShell, Python 3.11+)

**Browser interface:** With the database built, run `py -3 explorer.py january.sqlite` and open **http://127.0.0.1:8765/**. On the original development machine the existing database is available at `"$env:LOCALAPPDATA\Temp\opencode\checkpoint-jan.sqlite"`. The local server uses the Python standard library. Stop it with Ctrl+C.

Start with **Real detour**, expand its closure result, and inspect the note IDs and dates behind the replacement transfers. **Explore nearby** lists posts one or two transfers from your origin; select a destination to see its route. The date control uses the end of the selected UTC day. The stress test closes each page independently and reports the resulting distance change. These are pair-specific findings, not a ranking of globally important sources.

Download the five archives using the `$files` block in [research/README.md](research/README.md). From the repository root:

```powershell
py -3 route_map.py ingest january.sqlite @files
py -3 route_map.py route january.sqlite 1882827830331085172 1884646064566796739
py -3 route_map.py route january.sqlite 1882827830331085172 1884646064566796739 --close https://de.m.wikipedia.org/wiki/Demokratie
```

The example goes from one transfer to two. Each result includes the supporting note IDs. Use `--cutoff 2025-01-28T23:59:59Z` to ask the same question before the second endpoint's citations existed. To run tests, install `pytest` in your Python environment, then run `python -m pytest -q` from this directory.

## Checkpoint status

The instructor approved the topic change. January ingestion, shortest routes, evidence lookup, cutoff filtering, and single-page closures work from the CLI. The five archives produced 144,219 distinct citation records; the CLI reproduced both verified pilot cases, and four pytest tests pass. Scope remains January 2025. The neighborhood explorer, Streamlit views, scaling measurements, and closure-frequency analysis remain for the final submission.
