# Community Notes Route Map

SI 507 capstone | Initial project idea | November 17, 2026

**Question:** When two X posts are connected by a chain of pages cited in proposed Community Notes, does removing one page leave an equally short route, force a detour, or disconnect the posts?

The interface opens on a real pair of posts. A visitor follows the shortest chain, inspects the notes supporting it, and closes a transfer point to see what changes. A route shows citation reuse, not author influence, agreement, or evidence that a note was displayed to readers.

## Data and pilot

Use the Notes TSV file(s) from one dated [official Community Notes snapshot](https://x.com/i/communitynotes/download-data). The [schema](https://github.com/twitter/communitynotes/blob/main/documentation/under-the-hood/download-data.md) documents `tweetId` (annotated post), `noteId` (evidence record), `createdAtMillis` (UTC note creation time), and `summary` (note text containing the URLs). Store IDs as strings. No original post text or live API is required.

1. Select all notes created in January 2025 UTC. Record the snapshot date, filenames, checksums, filter, and row counts. Later snapshots can omit deleted notes; results describe only the selected snapshot and window.
2. Extract URLs from summaries. Retain original URLs alongside normalized keys. Lowercase the hostname and remove known tracking parameters; preserve identifiers such as YouTube's `v=` value. Flag unresolved short links rather than guessing their destination. Audit a sample of merged and unmerged URLs.
3. Count posts, cited pages, pages reused across distinct posts, and posts connected to another post. Manually verify a pair that disconnects and another that has a longer backup route. If January is too sparse, expand to January–March and report why.
4. Before committing to the topic academically, search research papers, public projects, and citations for post–source networks, alternate citation routes, and single-page dependencies in Community Notes. Record the closest work and the precise unanswered question. Novelty is a requirement, not a finding already established.

## Graph and route contract

Store an undirected bipartite graph: `post A → cited page 1 → post B → cited page 2 → post C` is two transfers. Each post–page edge retains the notes supporting it. Repeated citations add evidence, not extra edges. At a cutoff, include an edge only if at least one supporting note was created by that time within the window. This is a snapshot, so hop timestamps need not increase along a path.

Use breadth-first search on adjacency lists to minimize transfers. Rerun it with the selected page excluded to classify the closure as **same distance**, **longer detour**, or **disconnected**. On a prepared graph, each search takes O(V + E) worst-case time. Compare this design with a post-only graph: one page cited by 1,000 posts needs 1,000 post–page edges but can create 499,500 post pairs. A post-only representation must also track which shared pages still support each pair after a closure.

## Interface and implementation

| Streamlit view | User action | Result |
| --- | --- | --- |
| Find a route | Open a verified example or enter two post IDs/URLs and a cutoff. | Transfer count and a compact route diagram. Each hop reveals a supporting note ID, excerpt, date, and cited URL. |
| Explore from here | Choose a post and a radius of one or two transfers. | Reachable posts grouped by distance; selecting one opens its route. |
| Close a transfer | Exclude a cited page from the route, then optionally restore it. | Original and backup routes side by side, with the distance change or an explicit disconnected result. |

Use Python and SQLite for cleaned evidence, and keep graph operations independent of Streamlit. A `Citation` records one note's link to a page. A `CitationNetwork` enforces the two node types and implements route, neighborhood, and exclusion queries. Document invariants in class docstrings. The checkpoint can expose these operations through a CLI. The final landing screen should offer “Try a real detour” and “Try a fragile connection.”

## Evaluation and milestones

**Falsification line:** If exhaustive search on a small fixture finds a shorter eligible route, or the router returns a route containing an excluded page or supported only by a citation newer than the cutoff, the routing contract is broken.

| Stage | Deliverable |
| --- | --- |
| Proposal | Prior-work comparison, pilot data profile, two verified examples, target grade, draft contracts, and instructor approval for the topic change. |
| Checkpoint | Runnable ingestion and CLI routing; draft `SPEC.md`; at least three passing pytest cases covering minimum transfers, exclusion, and cutoff behavior; one-paragraph status note. |
| Peer audit | Ask a classmate to predict closure outcomes from the spec alone, including an equal-length backup. Revise ambiguous claims. |
| Final | Three Streamlit views, reproducible data-access instructions, finalized `SPEC.md`, discriminating tests, `AI_LOG.md`, and measured graph construction and query costs at increasing input sizes. |

For the final analysis, distinguish handpicked demo cases from measurement. Sample connected post pairs with a fixed seed, choose a shortest route using a documented tie rule, and exclude each cited page on that route in turn. Report counts and denominators for all three outcomes. Compare route lengths against exhaustive search on tiny graphs rather than requiring one particular path when several are equally short.

**Next step:** complete the prior-work check and data pilot. Dataset feasibility, novelty, and closure frequencies have not yet been established.
