# January study: replaceable links, fragile chains

**485 of 500 sampled connected post pairs (97.0%) depended on at least one cited page.** Removing that page left no route between those posts. Yet most individual removals left some route intact: 1,576 of 2,812 (56.0%). Several pages on a chain can be replaceable even when one page holds it together.

| After removing one route page | Trials | Share of trials |
| --- | ---: | ---: |
| Another equally short route survived | 643 | 22.9% |
| Only a longer route survived | 933 | 33.2% |
| The pair disconnected | 1,236 | 44.0% |

Percentages are rounded independently. Of the 500 pairs, 366 had an endpoint with only one cited page: its removal necessarily isolates that endpoint. But the effect was not limited to endpoints. For 228 pairs, removing a page strictly between the first and last pages of the chosen route also disconnected the posts. These groups can overlap.

## Method

Use the January 2025 UTC note window from the November 17, 2026 snapshot and the URL rules in [SPEC.md](../../SPEC.md). The frame is 140,465,276 distinct unordered connected post pairs in 5,151 components with at least two posts. A component of size s contributes s(s−1)/2 pairs. Sampling 500 distinct integer ranks (seed 507) makes each eligible pair equally likely without materializing the entire frame. Large components are intentionally sampled more often.

Route from the lower string ID using BFS with sorted neighbors. Close each page on that shortest route independently, restoring the graph between trials. A page outside the route cannot be indispensable to that pair: the original path would survive. Tie selection can affect which replaceable pages are tested. Trial percentages weight longer routes more; the pair percentage counts each pair once. CSV rows for a pair follow route order.

These estimates describe connected pairs under one month's citation and URL rules. They do not measure all X posts, source credibility, or independent evidence.

## Follow-up: remove the whole site

Among the **1,576** page-removal trials with a surviving backup, **995 (63.1%)** disconnected when all pages on that registrable domain were excluded instead. A further **45 (2.9%)** required a longer backup; **536 (34.0%)** retained a backup of the same length. The reference distance is the page-only backup distance. These are matched trials on the same January network, not a new sample.

The 1,576 rows correspond to 1,052 distinct `(post pair, site)` queries: several pages on one route can belong to the same site. Moreover, `x.com` accounted for **824 of the 995** lost backups. This finding is about the sampled routes, not a typical website. Only cited page nodes were excluded; both X post endpoints remained in the graph.

Run `py -3 -m research.site_study january.sqlite` to regenerate the [matched rows](site_closures.csv) and [site summary](site_summary.json) from `closures.csv`. The app links to a sampled example of each outcome.

## Representation benchmark

The full bipartite graph stored **140,319 post–page edges**. The post-only projection required **9,820,538 post–post edges** (about **70×** as many), plus the pages supporting each pair. Construction took **0.42 seconds vs. 17.64 seconds** in one local run. The evidence is strongest for construction cost and edge count, not a universal query speedup.

The [benchmark table](benchmark.csv) covers January prefixes of 1, 3, 7, 14 and 31 days. Build times exclude database reads; the bipartite structure also keeps an evidence witness and sorted neighbors. Query times are medians for 32 fixed-seed connected pairs per prefix, each closing its first page. Isolating an endpoint often makes those queries cheap. Both implementations agreed on distance or disconnection for all 160 queries. Wall-clock times vary by machine.

## Reproduction

From the repository root, using the January SQLite database:

```powershell
py -3 -m research.closure_study january.sqlite
py -3 -m research.benchmark january.sqlite
python -m pytest -q
```

The [trial table](closures.csv) includes both endpoints, the removed page, before/after distances and the outcome. The [summary](summary.json) drives the app. For each outcome the UI links to the example with the shortest original route in the sample (first sampled on ties). Tests check the trial denominators and independently enumerate simple paths across all 512 possible three-post, three-page networks with and without closures.
