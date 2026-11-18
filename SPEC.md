# Community Notes Route Map — checkpoint contract

Given two decimal X post IDs, an inclusive cutoff instant and optionally one excluded normalized page URL, return a minimum-transfer route in the frozen citation network. For each adjacent post/page pair, return one eligible witness (note ID, original cited URL, and creation time in UTC epoch milliseconds). This measures citation reuse, not information flow, agreement, or note visibility.

## Data contract

Read the five Notes TSV archives from X's November 17, 2026 snapshot ([source and reproduction instructions](research/README.md)). Select `2025-01-01 ≤ createdAtMillis < 2025-02-01`, interpreted as UTC dates. Keep `tweetId` and `noteId` as decimal strings; extract explicit HTTP(S) URLs from `summary`. The pilot's frozen normalizer lowercases hosts, drops fragments and `utm_` parameters, retains paths and other query parameters, and flags common shorteners for exclusion. It does not fetch target pages. The network cannot infer missing links or restore deleted notes. SQLite retains distinct citations; repeated notes citing the same page on the same post create only one graph edge.

## Routing rules

For clarity, the pilot's shortener rule excludes exactly the hosts `t.co`, `bit.ly`, `tinyurl.com`, and `ow.ly` (case-insensitive); it does not discover redirects or mark each rejected row in SQLite. A page-key collision is not evidence that two documents have identical contents.

- An eligible edge connects an annotated post to a page cited by at least one note created at or before the cutoff. The cutoff defaults to the last millisecond of January. Hop times need not increase.
- A transfer is `post → page → post`. Only posts with eligible citations are queryable. A present post reaches itself in zero transfers. An absent or unreachable endpoint yields `path: null`, `transfers: null`, and no evidence.
- Closing a page excludes it for that query only. The route may stay equally short, grow longer, or disappear. For ties, BFS visits neighbors in ascending string-key order.
- The browser neighborhood groups distinct destinations by minimum transfer distance (one or two), excluding the origin. Counts include every destination; at most 25 IDs are shown per group.
- Stress testing independently excludes each page on the selected shortest path, returning a backup and transfer delta or a disconnected result. With k pages on the path this takes at most k additional BFS traversals. The web interface caches one end-of-day snapshot. Deterministic neighbor ordering adds a one-time sorting cost of O(sum of degree(v) log degree(v)) during snapshot preparation.

## DS&A decision

**Connection history:** For two posts, return the earliest instant within the selected January snapshot at which *any* eligible citation chain exists. Use the earliest supporting note time on each edge regardless of input order. The activation time of a path is the maximum of its edge times; minimize that maximum using a priority queue. When a post is queried against itself, its first eligible citation establishes its presence. Return no result for an absent or disconnected pair. At the winning instant run thresholded BFS to select the shortest route available then, with the usual sorted-neighbor tie rule. The two stages take O((V+E) log(V+E)) time and O(V+E) auxiliary space with lazy heap entries. This dates a snapshot connection, not the transmission of information. A slower exact reference rebuilds the graph and runs BFS at every distinct event time.

BFS on the undirected bipartite adjacency lists minimizes edges and thus transfers (each transfer has exactly two edges). Given R eligible evidence records, graph construction takes expected O(R) time; the graph and one witness per edge use O(V+E) space for V nodes and E distinct connections. On the prepared graph, a query scans at most O(V+E) in time and uses O(V) extra space, including parents. The checkpoint CLI rebuilds the graph per invocation; timings of an entire command therefore include database loading.

A post-only graph gives O(P+L) BFS for P posts and L projected links, but must process a pair for every two posts citing each page during construction: a page with 1,000 posts creates 499,500 pair contributions instead of 1,000 edges. To handle closures the projection must retain supporting pages per pair or rebuild; deleting every pair supported by the closed page would erase valid equal-length backups.

**Falsification line:** If exhaustive search on a small graph disagrees about minimum transfer count or reachability, or a result uses the excluded page or an edge supported only after the cutoff, the routing contract is broken.

**Empirical evaluation:** The [January closure study](research/study/FINDINGS.md) documents the sampling frame, seed, denominators and measured build/query costs. The findings view links to trials at the study's January 31 cutoff.
