# Internal contract audit — November 18

This is an implementation self-review. The course participation audit still needs a classmate's own written feedback.

| Course question | Finding | Action |
| --- | --- | --- |
| Could someone write a test from the spec alone? | Route length, independent closures and the inclusive cutoff were concrete. “Common shorteners” did not specify which hosts count, or whether exclusion leaves a row. | Named the four hosts and specified what the database retains. |
| Which contract claim lacked a check? | The graph oracle starts with clean edges. It could pass even if ingestion merged different video IDs, admitted February rows, or dropped the original URL. | Added a small TSV-in-ZIP integration test that inspects actual SQLite rows at both month boundaries. |
| What plausible bug could the previous tests miss? | With repeated citations in unsorted input, keeping the first row encountered rather than the earliest timestamp could backdate or delay a history answer if that row were taken as the activation time. A second tempting shortcut is dating only the end-of-month shortest path. | Select the earliest witness regardless of input order; test a later direct shortcut against an earlier two-page connection. Compare all ordered post pairs on a small graph against rebuilt snapshots. |

**Remaining limitations for peer review:** URL variants can split a real page, and two source pages can repeat the same evidence. Neither a backup route nor the absence of one settles whether a claim is true. The January findings are estimates conditional on *connected* pairs, not on arbitrary X posts.
