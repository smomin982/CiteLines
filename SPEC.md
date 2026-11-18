# Community Notes Route Map — checkpoint contract

Given two decimal X post IDs, an inclusive cutoff instant and optionally one excluded normalized page URL, return a minimum-transfer route in the frozen citation network. For each adjacent post/page pair, return one eligible witness (note ID, original cited URL, and creation time in UTC epoch milliseconds). This measures citation reuse, not information flow, agreement, or note visibility.

## Data contract

The interactive graph, CLI and searches filter the archive to original IDs with oEmbed paragraph `lang=en` (or an `en-` regional variant) recorded in `data/english_posts.json`. Verification samples shared-source neighborhoods (`english_posts.py`); it does not infer original language from contributor wording. Unknowns are excluded. The earlier closure study still runs on the unfiltered archive and its aggregates are explicitly labeled.

Read the five Notes TSV archives from X's November 17, 2026 snapshot ([source and reproduction instructions](research/README.md)). Select `2025-01-01 ≤ createdAtMillis < 2025-02-01`, interpreted as UTC dates. Keep `tweetId` and `noteId` as decimal strings; extract explicit HTTP(S) URLs from `summary`. The pilot's frozen normalizer lowercases hosts, drops fragments and `utm_` parameters, retains paths and other query parameters, and flags common shorteners for exclusion. It does not fetch target pages. The network cannot infer missing links or restore deleted notes. SQLite retains distinct citations; repeated notes citing the same page on the same post create only one graph edge.

## Routing rules

**Original posts (display only):** Look up a decimal post ID through X's public oEmbed endpoint. Display its reported author, post paragraph and publication date as text; link to X for media and threads. A failed lookup means the preview is unavailable, not that the post is known to have been deleted. Live previews can differ from the January archive and do not participate in indexing, counting, or routing.

**Topic search:** SQLite FTS5's `unicode61` tokenizer indexes note prose with explicit HTTP(S) URLs removed. A word or multiword input is a literal phrase of adjacent tokens, not a Boolean expression or semantic match. A page counts a post once if at least one eligible note on that post both matches the phrase and cites that page. Results sort by descending distinct matching posts and then normalized URL, 20 at a time. Excerpts use the matching note (smallest stored note rowid among eligible witnesses for the group). The topic constrains discovery; the resulting route and closure experiments use all eligible citations at the same cutoff.

**Evidence text:** New databases retain one original `summary` per citing note ID. The explorer shows the selected edge witness's text, with whitespace collapsed and at most 280 characters including the truncation marker. Excerpts come from proposed notes, not from annotated posts. Legacy databases without text keep the same graph results. Choosing a starting post on an article page is valid only if its note is eligible at the selected cutoff.

For clarity, the pilot's shortener rule excludes exactly the hosts `t.co`, `bit.ly`, `tinyurl.com`, and `ow.ly` (case-insensitive); it does not discover redirects or mark each rejected row in SQLite. A page-key collision is not evidence that two documents have identical contents.

- An eligible edge connects an annotated post to a page cited by at least one note created at or before the cutoff. The cutoff defaults to the last millisecond of January. Hop times need not increase.
- A transfer is `post → page → post`. Only posts with eligible citations are queryable. A present post reaches itself in zero transfers. An absent or unreachable endpoint yields `path: null`, `transfers: null`, and no evidence.
- Closing a page excludes it for that query only. The route may stay equally short, grow longer, or disappear. For ties, BFS visits neighbors in ascending string-key order.
- The browser neighborhood groups distinct destinations by minimum transfer distance (one or two), excluding the origin. Counts include every destination; at most 25 IDs are shown per group.
- Stress testing independently excludes each page on the selected shortest path, returning a backup and transfer delta or a disconnected result. With k pages on the path this takes at most k additional BFS traversals. The web interface caches one end-of-day snapshot. Deterministic neighbor ordering adds a one-time sorting cost of O(sum of degree(v) log degree(v)) during snapshot preparation.

## DS&A decision

**Source-first interaction:** A bare domain groups pages using the frozen registrable-domain rules. A full HTTP(S) URL is matched by the same page-key normalizer used at ingestion. Search uses only the cutoff graph, counts distinct post neighbors per page and orders results by descending count then ascending URL, 20 per results page. Pair comparisons from a source page require two different citing posts. When several URLs directly connect that pair, the page experiment can use the visitor's selected shared page rather than the default BFS tie winner.

**Matched site study:** Repeat site closure for every surviving trial in `closures.csv`. Retain a row per original trial, even when several rows share a pair and site; compare the new distance with the page-only backup. Counts are conditional on the original page closure leaving a connection.

**Site comparison:** Select a page on the displayed shortest route. Compare two independent BFS searches at the same cutoff: one excludes only that page, the other excludes all cited pages with its registrable domain. A lazy index maps each domain to its page nodes; the site trial skips those nodes and leaves post nodes intact. The bundled Mozilla Public Suffix List (ICANN and private sections, version 2026-11-17) defines domain boundaries offline. For example `news.bbc.co.uk` and `sport.bbc.co.uk` share a site, but `alpha.github.io` and `beta.github.io` do not. Site closure cannot shorten the page-only backup or restore a disconnected pair. The existing 500-pair study measures single-page removal only.

**Connection history:** For two posts, return the earliest instant within the selected January snapshot at which *any* eligible citation chain exists. Use the earliest supporting note time on each edge regardless of input order. The activation time of a path is the maximum of its edge times; minimize that maximum using a priority queue. When a post is queried against itself, its first eligible citation establishes its presence. Return no result for an absent or disconnected pair. At the winning instant run thresholded BFS to select the shortest route available then, with the usual sorted-neighbor tie rule. The two stages take O((V+E) log(V+E)) time and O(V+E) auxiliary space with lazy heap entries. This dates a snapshot connection, not the transmission of information. A slower exact reference rebuilds the graph and runs BFS at every distinct event time.

BFS on the undirected bipartite adjacency lists minimizes edges and thus transfers (each transfer has exactly two edges). Given R eligible evidence records, graph construction takes expected O(R) time; the graph and one witness per edge use O(V+E) space for V nodes and E distinct connections. On the prepared graph, a query scans at most O(V+E) in time and uses O(V) extra space, including parents. The checkpoint CLI rebuilds the graph per invocation; timings of an entire command therefore include database loading.

A post-only graph gives O(P+L) BFS for P posts and L projected links, but must process a pair for every two posts citing each page during construction: a page with 1,000 posts creates 499,500 pair contributions instead of 1,000 edges. To handle closures the projection must retain supporting pages per pair or rebuild; deleting every pair supported by the closed page would erase valid equal-length backups.

**Falsification line:** If exhaustive search on a small graph disagrees about minimum transfer count or reachability, or a result uses the excluded page or an edge supported only after the cutoff, the routing contract is broken.

**Empirical evaluation:** The [January closure study](research/study/FINDINGS.md) documents the sampling frame, seed, denominators and measured build/query costs. The findings view links to trials at the study's January 31 cutoff.
