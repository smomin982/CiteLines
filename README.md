# Community Notes Route Map

**English originals only:** The interactive explorer and CLI use a curated set of 160 original posts that X tagged as English in its public embed. Unknown, unavailable-at-verification, and non-English originals are excluded from search counts and every routing hop. This is a verified subset, not a census of all English posts. Notes and external source pages are separate content and are not translated. The original multilingual archive stays intact for study reproduction.

**Start with the posts:** The walkthrough shows the two original X posts side by side, their shared citation, then a page-removal experiment. Text previews use X's public oEmbed service and include the reported author and date. Open the permalink for media or the live thread. Other result lists load previews on demand. A blocked or unavailable post does not prevent exploring locally archived notes.

**Search by topic:** Choose **Search by topic**, enter a word or an exact phrase (for example `gambling`), and open a cited page. Select two posts from the matching excerpts to try a route, a closure, or connection history. Counts describe matching posts only; routing uses the full graph at your cutoff. New ingestions build the SQLite FTS5 index automatically. For an existing database with note text, run `py -3 topic_search.py january.sqlite` once. Databases without note text need a fresh ingestion.

**Explore by source:** Start with a domain such as `bbc.co.uk` or paste a full article URL. Browse exact pages ranked by distinct citing posts, select two posts, and compare their route, connection history, or page/site closures. The comparison shows the original, page-removed and site-removed routes together.

On an article's page, read the proposed note excerpts, click **Start with this post**, then choose **Compare page vs. site**, **View route**, or **See connection history** under another post. Your first choice stays selected across pages. New databases built with `route_map.py ingest` include the original note text; existing databases still work, but display an unavailable-text label until rebuilt under a new filename.

**One page or the whole site?** On a route, choose the page/site comparison to run the closures independently.

**Connection history:** Choose **When did these posts first connect?** on a route to compare the shortest chain at the first recorded connection with the chain at the selected cutoff.

**[January research findings](research/study/FINDINGS.md):** 485 of 500 sampled connected pairs depended on at least one cited page. Select **What we found** in the explorer to compare the 2,812 individual page removals and inspect real examples.

Trace the shortest citation chain between two X posts and close a page to see whether the connection survives. The [approved proposal](PROPOSAL.md) describes the project, and [SPEC.md](SPEC.md) defines the checkpoint behavior.

## Run the checkpoint (PowerShell, Python 3.11+)

**Browser interface:** With the database built, run `py -3 explorer.py january.sqlite` and open **http://127.0.0.1:8765/**. On the original development machine the existing database is available at `"$env:LOCALAPPDATA\Temp\opencode\checkpoint-jan.sqlite"`. The local server uses the Python standard library. Stop it with Ctrl+C.

Start with the SpaceX funding or Los Angeles wildfires walkthrough. Follow the chain, then click **Remove that page and see what happens**.

Download the five archives using the `$files` block in [research/README.md](research/README.md). From the repository root:

```powershell
py -3 route_map.py ingest january.sqlite @files
py -3 route_map.py route january.sqlite 1880029118080942296 1880032372437184730
```

Each result includes the supporting note IDs. Use `--cutoff` to select a UTC instant. To run tests, install `pytest` in your Python environment, then run `python -m pytest -q` from this directory.

## Checkpoint status

The instructor approved the topic change. January ingestion, shortest routes, evidence lookup, cutoff filtering, and single-page closures work from the CLI. The five archives produced 144,219 distinct citation records; the CLI reproduced both verified pilot cases, and four pytest tests pass. Scope remains January 2025. The neighborhood explorer, Streamlit views, scaling measurements, and closure-frequency analysis remain for the final submission.
