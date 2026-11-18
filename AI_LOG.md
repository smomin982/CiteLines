# AI build log

## 2026-11-17 — Topic selection and initial plan

- **Request:** Initialize the repository, brainstorm capstone ideas, check related work, and plan a network-routing project using X Community Notes.
- **Kept:** The post–page graph, shortest-route and page-closure comparison, and three exploration modes. They make the routing decision visible and let users inspect the note behind each connection.
- **Changed:** Moved away from F1 and subreddit pathfinding after considering personal interest and overlap with existing work. Reframed the X citation idea around backup routes rather than counting repeated citations.
- **Open:** Verify the originality of the specific research question and test whether real page reuse yields both fragile connections and detours before proceeding to the checkpoint.

## November 2026 — Research branch

- **Request:** Do the prior-work review and January feasibility pilot on a separate branch.
- **Method:** Compared related publications, graph datasets, and an existing dashboard. Selected the complete set of Notes shards for one snapshot and designed an offline scan with page-level keys, evidence IDs, and a second raw-row check of the selected examples.
- **Decision:** Keep the originality claim limited to the scoped search; keep demonstration cases separate from any estimate of closure frequency.

### Proposal drafting

- **Request:** Proceed from the committed feasibility pilot to the topic-change proposal.
- **Draft choices:** Used the verified German detour as the opening example and scoped delivery to January because the pilot already demonstrates both closure outcomes. Included the verified counts and qualified prior-work claim; left closure frequencies as a research question. Target grade A is proposed for student review. Instructor approval is pending.

### 2026-11-17 — Approval and checkpoint

- **Update:** The student reported instructor approval. The assistant implemented the planned CLI checkpoint on a new branch.
- **Kept and checked:** Reused the pilot URL keys to preserve comparability. Added SQLite evidence storage, BFS routing, cutoff and closure tests. Checked both pilot pairs against the CLI before and after closure. Left stable tie selection and the broader empirical analysis for the final build.

### 2026-11-17 — Explorer enhancement

- **Request:** Enhance the checkpoint app. Added a local browser interface, bounded neighborhoods and independent closure trials along a selected route.
- **Design choice:** Use a standard-library local server rather than require Streamlit, so the same Python installation and existing SQLite database run both interfaces. Sort adjacency lists once for repeatable tie selection; keep closure trials independent so an early disconnection cannot contaminate later results.
