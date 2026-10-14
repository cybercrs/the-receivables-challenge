# Final student-facing JavaScript app validation

October 14, 2026. Development files remain in `native-pilot/` on the source branch. The approved public destination is `https://cybercrs.github.io/the-receivables-challenge/js/`. The publishing branch moves the native app to `js/` and removes the old published `native-pilot/` directory entirely, with no redirect, as requested. No Pages settings, main branch, old Python/Streamlit code, or existing stlite browser-root files are changed.

| Check | Result | Evidence |
| --- | --- | --- |
| Existing unit/AppTest suite | Passed: 25 | [unit.log](review/unit.log) |
| Native calculation, codec, shuffle, migration and curriculum tests | Passed: 13 groups | [parity.log](review/parity.log) |
| Actual Chromium revised lesson and bookmark walkthrough at `/the-receivables-challenge/js/` | Passed: 11 groups | [browser-results.json](review/browser-results.json), [browser.log](review/browser.log) |
| Native Python tooling Ruff, JS syntax, whitespace | Passed | [lint.log](review/lint.log), [whitespace.log](review/whitespace.log) |
| All non-native source files | Byte unchanged: 47 | [source-protection.json](review/source-protection.json) |
| Published layout, hashes, relative assets and removed route | Passed | [route-build.json](review/route-build.json), [site-build.log](review/site-build.log) |
| Final title, student-facing wording, metadata and generated content | Passed | [final-branding-audit.json](review/final-branding-audit.json) |
| Hosted browser, real-device/browser matrix and classroom concurrency | Not run | Known proxy restriction respected |

Both aging schedules are transposed: age-bucket column headers, fixed Accounts receivable/Estimated loss rate/Estimated uncollectible rows, and a complete Total column. Original numerical assumptions and numbered cells remain. On narrow screens, horizontal scrolling retains sticky measure labels and totals. Cell directions and explanations follow the new axes. Table expansion and CSV retain the complete three-row/seven-column data.

Only the duplicate required ending allowance question is removed. The adjustment, expense increase, net realizable value, and conceptual aging response remain. All valuation feedback variants omit the premature flat-rate method comparison. The final discussion introduces an explicitly labeled 8% flat-rate illustration and describes why well-supported age-specific rates can be more informative without promising automatic accuracy.

The denominator is now 26 checkpoints; valuation has four. The deliberate wrong-claim/revised-calculation flow yields **22/26 first-pass correct with five revisions**. Read-only review preserves the canonical snapshot, and Forward stops at the actual frontier. Pre-update native v3/v4 and original Python bookmarks retain all remaining answers, drafts, seeds and earned positions. Only retired question scoring/drafts are dropped; an old wrong answer to that removed question does not block otherwise completed retained work. The original wire allowance value is normalized to the now-given total without earning a new score or advancing a page.

The tests exercise full completion, current-page mistakes, repeated checks, invalid and formatted numeric draft refresh, final dropdown wording, old completed and in-progress bookmarks, future-view rejection, reset, independent contexts, keyboard navigation, full backward/forward review, desktop and 390-pixel schedule layouts, pinned total cells, table expansion and CSV. Zero external requests, console errors and page errors were recorded.

The browser tab title is now **The Receivables Challenge**, without provisional app branding. Every loaded page checks the exact title, rendered wording, accessibility labels, tooltip text, and metadata. The audit covers all 25 generated lesson positions in 75 unanswered/incorrect/correct variants, including headings, banners, help, footer/save note, downloads, and final discussion. No manifest or social title contains provisional wording. The accounting phrase “test an early-payment discount” remains. Running the exporter leaves the HTML entrypoint and generated content unchanged; rebuilding copies the final title. Only `index.html` changes among the six runtime files. The other five files match source commit `d8130a23f7d5e079ed3de9654362ca32437d4622`; teaching content, calculations, navigation and saved progress are unchanged. The published provenance description is finalized as “student-facing native JavaScript app”.

The full walkthrough uses the repository-prefixed `/js/` path and verifies query parameters (including repeated and encoded values), fragments, saved drafts, review positions and relative asset loading. Original Python and older native progress payloads still restore when their path is changed to `/js/`. The removed `native-pilot/` and `native-pilot/index.html` routes return 404 locally. The generated site also contains only `js/`, with no redirect. Hosted old-route HTTP testing remains unavailable under the known proxy restriction; the exact deployed Git tree is checked separately for directory removal.

Screenshots: [first schedule desktop](review/aging-schedule-desktop.png), [first schedule narrow](review/aging-schedule-narrow.png), [second schedule desktop](review/valuation-schedule-desktop.png), [second schedule narrow](review/valuation-schedule-narrow.png), [completion](review/complete-desktop.png). Legacy native fixtures were produced from the previously published source commit `060cdb0332c6aeeb8e91cc1b974213a3ff552d83`.

The six native application assets total 204,756 bytes. Five cache-disabled loopback Chromium initializations measured 78.1 ms median (72.4–94.1 ms). These are local functional measurements, not school-network, physical-device or classroom-capacity guarantees.

Exact source/static commits and successful Pages deployment are verified after publishing and reported separately. The existing public stlite root remains intact.
