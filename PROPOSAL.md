# Community Notes Route Map

**SI 507 capstone proposal · Target grade: A · Approved by instructor (reported by student)**

Two X posts looked one transfer apart: notes on both cited the German Wikipedia article *Demokratie*. I wanted to know whether that page was a shortcut or the only connection. In the January 2025 pilot, removing it revealed a two-transfer detour: notes on a third post cited both a *Frankfurter Rundschau* article and the Bundestag's seat-distribution page. In another case, removing a shared biography left both posts isolated.

**Research question:** Among a reproducible sample of connected posts, when does removing one cited page from a shortest route leave an equally short route, force a longer detour, or disconnect the posts? Existing work examines the credibility and frequency of sources cited in notes. My [prior-work review](research/PRIOR_WORK.md) found no direct match for this page-removal measurement. The proposed contribution is an empirical answer, not a new routing algorithm.

## Dataset and draft data contract

I will use the Notes table from [X's public Community Notes export](https://x.com/i/communitynotes/download-data). I have a working pilot using all five Notes shards from the November 17, 2026 snapshot, filtered to notes created in January 2025 UTC. It found **113,274 notes about 77,256 posts**, with 13,482 normalized pages cited on multiple posts. The [pilot results](research/january.json) record file checksums, counts, and the note IDs supporting both examples.

Each citation connects the annotated post (`tweetId`) to an explicit HTTP(S) URL in the note text (`summary`). I will retain the original URL, normalized page key, supporting `noteId`, and note creation time (`createdAtMillis`). The normalizer lowercases hostnames and removes fragments and known tracking parameters while preserving page-identifying parameters, such as a video's ID. Known unresolved shorteners are excluded. Repeated citations support one connection rather than adding parallel routes. At a selected cutoff, a connection exists only if an eligible note supports it by that time.

A route represents shared citations in the frozen dataset. It does not establish that an author influenced another, that sources agree, or that a note was publicly displayed. An unreachable result applies only to the selected window and URL rules.

## DS&A decision and draft falsification line

I will use an undirected bipartite adjacency list: posts and cited pages are distinct node types. Breadth-first search (BFS) finds the fewest citation transfers; `post → page → post` counts as one. Rerunning BFS while skipping one page finds the best surviving route. For a prepared snapshot with \(V\) nodes and \(E\) unique connections, graph storage and each worst-case search are \(O(V+E)\).

The straightforward alternative is to connect posts directly when they share a page. One page cited by 1,000 posts requires 1,000 bipartite edges but generates 499,500 post pairs. Across pages of degree \(d_p\), building the projection requires processing \(\sum_p \binom{d_p}{2}\) pair contributions. BFS then costs \(O(P+L)\) for \(P\) posts and \(L\) distinct post-pair links. To simulate deletion correctly, the projection must remember which pages support each pair or rebuild after a deletion. I will benchmark build cost, graph size, and query time separately on increasing data slices.

**Falsification line:** If exhaustive search on a small fixture disagrees with the router about minimum transfer count or reachability, or a returned route uses an excluded page or an edge supported only after the cutoff, the routing contract is broken.

## Deliverable and scope

The final interface will be a local Streamlit app with three modes: **find a route** and inspect its supporting notes; **explore from a post** within one or two transfers; and **close a page** to compare the original route with its backup. The two verified examples will give visitors a starting point. Python classes `Citation` and `CitationNetwork` will separate stored evidence from graph behavior, with SQLite retaining provenance for each hop.

After approval, the checkpoint will include runnable ingestion and CLI routing, a draft `SPEC.md`, and pytest cases that distinguish disconnection from a longer detour, preserve an equal-length backup, and exclude future evidence. For the final analysis I will use a fixed-seed sample of connected post pairs, a documented tie rule for shortest paths, and one closure trial per page on the selected path. I will report counts and denominators separately from the handpicked demos. January is sufficient for the core project; with extra time I would repeat the analysis across months to test whether the findings persist.
