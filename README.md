# Community Notes Route Map

Trace the shortest citation chain between two X posts and close a page to see whether the connection survives. The [approved proposal](PROPOSAL.md) describes the project, and [SPEC.md](SPEC.md) defines the checkpoint behavior.

## Run the checkpoint (PowerShell, Python 3.11+)

Download the five archives using the `$files` block in [research/README.md](research/README.md). From the repository root:

```powershell
py -3 route_map.py ingest january.sqlite @files
py -3 route_map.py route january.sqlite 1882827830331085172 1884646064566796739
py -3 route_map.py route january.sqlite 1882827830331085172 1884646064566796739 --close https://de.m.wikipedia.org/wiki/Demokratie
```

The example goes from one transfer to two. Each result includes the supporting note IDs. Use `--cutoff 2025-01-28T23:59:59Z` to ask the same question before the second endpoint's citations existed. To run tests, install `pytest` in your Python environment, then run `python -m pytest -q` from this directory.

## Checkpoint status

The instructor approved the topic change. January ingestion, shortest routes, evidence lookup, cutoff filtering, and single-page closures work from the CLI. The five archives produced 144,219 distinct citation records; the CLI reproduced both verified pilot cases, and four pytest tests pass. Scope remains January 2025. The neighborhood explorer, Streamlit views, scaling measurements, and closure-frequency analysis remain for the final submission.
