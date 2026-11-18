# January 2025 feasibility pilot

**Result: both proposed demo cases exist in January alone.** In the November 17, 2026 snapshot, January contained 113,274 notes about 77,256 posts. The pilot found 140,319 distinct post–page connections; 13,482 of the 91,067 normalized pages appeared on multiple posts. Of all annotated posts, 36,353 could reach at least one other post under these rules.

| Closure | Evidence and outcome |
| --- | --- |
| Remove the Arabic Wikipedia biography of Said bin Sultan. | The two example posts each had only this one eligible cited URL. Both endpoints became isolated. |
| Remove the German Wikipedia page *Demokratie*. | The endpoints lost their only shared URL. A third post linked them via a *Frankfurter Rundschau* article and the Bundestag seat-distribution page instead: one transfer became two. |

All eight edge witnesses across these examples used identical raw and normalized URLs; neither result relies on merging URL variants. The independent source-row check passed for both. See `january.json` for exact posts, notes, timestamps, and checksums. In the wider normalization sample, fragment removal correctly grouped section links at page level and different BBC articles stayed distinct. HTML-escaped query separators and mobile/desktop variants merit further work before estimating population rates.

`pilot.py` filters one cumulative snapshot, not one file per day. Use Python 3.11+ and the five Notes ZIPs under `https://ton.twimg.com/birdwatch-public-data/2026/11/17/notes/`. Run from the repository root. Example in PowerShell (keep raw data outside Git):

```powershell
$cache = Join-Path $env:TEMP 'community-notes-20261117'
New-Item -ItemType Directory -Force $cache | Out-Null
$files = foreach ($i in 0..4) {
    $name = 'notes-{0:D5}.zip' -f $i
    $path = Join-Path $cache $name
    curl.exe -fLsS --retry 2 -o $path "https://ton.twimg.com/birdwatch-public-data/2026/11/17/notes/$name"
    if ($LASTEXITCODE) { throw "Could not download $name" }
    $path
}
py -3 research/pilot.py @files --out research/january.json
py -3 research/verify_examples.py research/january.json @files
```

`january.json` contains member names, ZIP checksums, counts, sampled normalization decisions and route witnesses. A citation transfer goes from one post to another via a page. The graph includes explicit HTTP(S) URLs found in note text; it does not infer bare domains, follow redirects, or aggregate pages by publisher. Common shorteners are excluded. Removing fragments treats sections of the same document as one page; tracking-parameter removal preserves other query parameters. URL keys are operational approximations, not verified content identities.

Example selection favors low-degree shared Wikipedia pages to produce readable examples, then other pages. These examples cannot estimate the frequency of closure outcomes. The independent verification pass rereads source rows, checks note IDs and exact cited strings, and examines each endpoint's entire set of eligible pages. It checks the disconnection and that a detour exists but no single-transfer backup survives; the BFS in the discovery script computes shortest distance.
