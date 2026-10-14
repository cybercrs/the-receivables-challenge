# Native Receivables pilot validation

Local validation completed October 14, 2026 in Accounting Teaching Apps. Publication is **pending explicit user approval**. No native source branch or preview has been pushed. Proposed preview: `https://cybercrs.github.io/the-receivables-challenge/native-pilot/`, appending only that unused directory on `stlite-browser` without changing Pages settings or the current root app.

| Check | Result | Evidence |
| --- | --- | --- |
| Existing unit/AppTest suite | Passed: 25 | [unit.log](review/unit.log) |
| Native calculation, codec, shuffle, validation and scoring tests | Passed: 10 groups | [parity.log](review/parity.log), [Python oracles](tests/python-oracles.json) |
| Actual Chromium browser walkthrough | Passed: 8 groups | [browser-results.json](review/browser-results.json), [browser.log](review/browser.log) |
| Ruff for native development/test tools | Passed | [lint.log](review/lint.log) |
| Source preservation | All 45 original tracked files except the append-only ignore list are byte unchanged | [source-protection.json](review/source-protection.json) |
| Hosted UI, real devices/browser matrix, classroom concurrency | Not run | Known Pages hostname proxy restriction respected; publication pending |

Calculation parity covers all aging rows, gross/allowance/net values, method comparison, five write-off amounts, and all liquidity metrics. Ten monetary formatting edge cases verify Python ties-to-even rounding. All 115 option-order fixtures match Python exactly, including seeds above JavaScript's safe integer range. Old saved snapshots at every stage decode exactly. New ordinary snapshots are accepted by the original Python validator, including the maximum 63-bit seed.

The browser run completed all 25 pages/22 choice decisions, deliberately selected a wrong claim twice, corrected it, deliberately submitted wrong valuation amounts, repeated an unchanged valuation, and then completed the case. The resulting first-pass score was **22/27 with six revisions**, matching Python's score summary. It tested original reveals, calculation gating, write-off balances, all four debrief disclosures, table sorting/expanded viewing/CSV, choice and formatted/unfinished numeric drafts, refresh/bookmarks, a full immutable review in both directions, future-view rejection, invalid snapshots, independent tabs and contexts, reset, keyboard focus/Enter, and 44-pixel arrow targets.

Screenshots: [desktop briefing](review/briefing-desktop.png), [write-off](review/writeoff-desktop.png), [desktop completion](review/complete-desktop.png), [desktop review](review/review-desktop.png), [narrow completion](review/complete-narrow.png), [narrow review](review/review-narrow.png). CSV evidence is in `review/valuation-table.csv` and `review/review-table.csv`.

## Measured native startup and size

The six application assets total **202,614 bytes (197.9 KiB)**. A hash/provenance manifest is packaged separately. They contain no Python, Pyodide, Streamlit, WebAssembly runtime, framework bundle or external asset dependency. The previously deployed stlite app remains at the root and is not downloaded by this pilot.

Five fresh cache-disabled Chromium contexts on local loopback measured readiness from navigation at **86.4 ms median**, **79.3–91.1 ms range**. Timing includes importing the JavaScript case/screens, restoring/initializing progress, rendering and saving the initial URL. These are cloud loopback measurements, not hosted-network, physical-device, school bandwidth, or classroom-capacity claims. The full individual runs and resource byte counts are recorded in `browser-results.json`.

No console errors, page execution errors or external HTTP requests occurred. Browser traffic outside loopback was blocked by a closed test proxy; no TLS exception or alternate route to the restricted Pages host was used.

## Fidelity and limits

Original instructional content, calculations, balances, scoring rules, numeric bounds, feedback/reveal gates and downloads are preserved. Native system fonts and HTML widgets replace framework chrome. Current browsers must support ES modules, BigInt, Web Crypto, structured cloning and Compression Streams. Chromium is validated; other browsers/devices remain untested.

Native numeric drafts can retain grouped currency and unfinished numeric text without silently rounding or persisting arbitrary identifying text. The original format supports saved attempt counts only through 99; the pilot preserves higher repeated-practice scores by upgrading only overflow snapshots to native version 4. These exceptional extended links resume in the native pilot, while ordinary links remain version-3 compatible. The older app does not support version 4.

All remote mutations are paused per the latest instruction until explicit publication approval. Once approved, push the isolated source branch and append the tested native package only under `native-pilot/` on the existing static branch. Verify the complete baseline publishing tree is unchanged, then confirm the exact GitHub Pages deployed commit through the connector. No merge to main or Pages configuration change is needed.
