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

### 2026-11-17 — First-visit redesign

- **Feedback:** The neighborhood screenshot exposed IDs and transfer counts without explaining what they meant.
- **Change:** Lead with a guided example; label the two posts by what their proposed notes discuss, checked against the eight original witness summaries. For other destinations, identify the cited source instead of guessing the post's subject. Keep IDs, note dates, and raw evidence available on demand.

### 2026-11-18 — Closure study and defense evidence

- **Request:** Execute the 500-pair study, publish its findings in the interface, and benchmark the design.
- **Choices:** Sample uniformly over connected unordered post pairs. Use independent closures and report pair and trial denominators separately. Keep the trial evidence in CSV, compare two exact representations on five prefixes, and check BFS against independently enumerated paths.
- **Finding:** Pair-level fragility coexists with most individual removals leaving a route intact. Report both denominators and identify the contribution of single-page endpoints.

### 2026-11-18 — Internal audit, defense practice and connection history

- **Request:** Continue the contract review and defense preparation, defer the classmate exercise and packaging, and develop additional features.
- **Kept:** An internal audit with source-to-database checks and an interactive first-connection view. The earliest complete chain can precede the current shortest chain; compare against rebuilding each snapshot on a small graph. Practice prompts tie design choices to actual measurements. External feedback remains pending.

### 2026-11-18 — Page versus site closures

- **Request:** Proceed with the proposed site-dependence feature after the history commit.
- **Decision:** Compare two independent closures at the same cutoff using the bundled public suffix rules, rather than treating a hostname or publisher name as a site. Verified a sampled pair where a six-page backup survives removal of the specific page but no backup survives removal of its domain.

### 2026-11-18 — Explore by source and measure site dependence

- **Request:** Build a source-first entry point, run the matched site study, and show three compact route states.
- **Decisions:** Count distinct posts, not notes. Preserve the visitor's selected shared page for closure comparisons, even when another URL wins a shortest-path tie. Reuse all surviving trial rows and cache identical pair/site queries without collapsing their statistical weights. Report the concentration of lost backups on `x.com` alongside the overall rate.

### 2026-11-18 — Evidence-first pair selection

- **Request:** Continue implementing the source-first explorer.
- **Kept:** Store original summaries locally once per note, attach excerpts to dated witnesses, and select posts directly from their note cards. Older databases remain readable. Showing contributor wording avoids inventing a description of an unavailable original post.

### 2026-11-18 — Topic-first exploration

- **Request:** Implement indexed word/phrase search, matching-post counts and a path from topic discovery into existing experiments.
- **Follow-up:** Added live original-post previews after the user reported that note excerpts alone made the interface hard to understand. Verified oEmbed availability for both guided pairs and separated the author’s text, contributor note, and shared source in the walkthrough.
- **Language scope:** At the student's request, limited visitor-facing post discovery and routing to verified English originals. Used X's language tag, changed the guided examples, and preserved the original research denominators separately.
- **Interface iteration:** Reworked the walkthrough as an interactive citation atlas. Its diagram links to the two posts and the actual shared page; the same visual system now covers search, closure outcomes, and study findings.
- **Topic results:** Added X's native embedded post alongside the exact contributor note used as each page's search witness. One note can support multiple page results; the post is not selected independently of the note. Verified the wildfire result renders a native X iframe.
- **Topic coverage:** Replaced three static examples with positive-count suggestions grouped by interest. Selected additional candidates from matching notes across the month and checked original-post language before admission. Added a full-month option for restrictive cutoffs.

### 2026-11-24 — Resume topic coverage

- **Request:** Check the running app and finish the topic-coverage work.
- **Decision:** Keep the verified English collection and preserve the exact phrase when widening the date range. Label the archived study with its original export date, independently of the explorer database.

### 2026-11-24 — Interactive map and verified examples

- **Request:** Make source removal interactive and offer entry points by outcome.
- **Decisions:** Compute original and independent closure states from the same cutoff graph; update only the route and evidence in the browser. Recheck case labels against the loaded English graph rather than displaying outdated outcomes from the multilingual study.
- **First-visit feedback:** The student found the map confusing and the interface bland. Added an annotated A–source–B diagram, one prominent first action, and plain-language outcomes. Keep contributor notes separate from original posts and explain that simulated removals do not change X.
- **Typography:** Replaced Georgia with Manrope for headings and Source Sans 3 for interface text. Bundled the fonts and their Open Font Licenses so the local app does not need to contact a font service. Embedded X posts retain X’s typography.
- **Presentation goal:** The student chose first-minute comprehension for classmates. Kept the live click and added a before/after reveal instead of asking viewers to remember the original route. Moved site removal to a follow-up and added a rehearsal cue to the README.
- **Decisions:** Use SQLite FTS5 with literal phrase matching; remove URL strings before indexing. Join citations by note ID so unrelated notes on the same post cannot contribute pages. Keep work offline, support indexing an existing text-enabled database and use one local server.
