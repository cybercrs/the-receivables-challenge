# Native Receivables browser pilot

This is an isolated HTML/CSS/JavaScript implementation of The Receivables Challenge. It contains no Python interpreter, Streamlit, Pyodide, WebAssembly runtime, npm runtime dependency, external asset request, or installation step. The delivered activity is six native files plus a hash manifest; Python and Node are development/test tools only.

The source branch is `pilot/native-receivables`, based on the accepted `rollout/stlite-browser-navigation` commit `81f1411b256f635b7c31698b81a32c68b91ca4fa`. Main and the existing browser implementation remain unchanged. The preview is appended only under `native-pilot/` on the existing `stlite-browser` publishing branch. Its root URL and every unrelated publishing file are preserved. No Pages setting, credential, repository, or server deployment is changed.

## Instructional fidelity

`export.py` reads the unchanged Python case data and captures the original teaching renderers at all 25 positions in unanswered, incorrect, and correct states. The resulting `content.js` contains the original 22 choice decisions, scenarios, prompts/options, explanations, account and statement effects, numeric valuation instructions and feedback, numbered aging cells, balance comparisons, dashboard, scoring labels, and four debrief questions/model answers. It is generated rather than manually rewritten. There are no app-owned image assets or prebuilt download files in the source lesson.

Native tables retain all original data, column headings, numbered cells, totals, sorting, expanded viewing, and CSV download. Write-off before/after balances and dashboard figures preserve the original presentation and calculations. Native system fonts and accessible HTML controls replace framework widgets; the original theme CSS is reused. No instructional feature is omitted.

`engine.js` independently calculates aging totals and allowance rows, percentage estimates, valuation, write-offs, average net receivables, turnover and collection period. Whole-dollar display uses Python-compatible ties-to-even rounding. Input accepts whole-dollar digits, valid grouped commas and a leading dollar sign; fractions, incomplete commas, negative amounts, non-numeric text and out-of-range values cannot be submitted. Increment buttons keep the original 100-dollar step without requiring answers to be multiples of 100.

## Progress and review

The original validated compressed version-3 `progress` URL snapshots are supported, including exact 63-bit seeds. Python-compatible SHA-256 seeding, MT19937 and shuffle behavior preserve the exact option order of old saved work. Native version-3 links in the original supported range can also be decoded by the unchanged Python validator. To try an old bookmark, retain its `progress` and `view` query parameters while changing the path to `/the-receivables-challenge/native-pilot/`.

A separate bounded `view` records review position. Back is strictly read-only: it exposes no answer inputs, checks, revisions, hints/reveals, score changes or activity reset. Forward traverses reached pages and stops at the earned current page even after a correct answer. Only an original validated Open, Continue or Finish action advances the frontier. The action model enforces these rules independently of disabled/hidden controls.

Choices, valid and unfinished numeric drafts, answers, first-pass flags and attempts survive navigation, refresh and bookmarks. A bounded optional `draft` parameter retains formatted and incomplete numeric text; arbitrary names/text are not persisted. Independent tabs and contexts begin independently without localStorage or a central save service. Reset is disabled during review and starts a fresh seed/activity on the current page. Older copied bookmarks remain their own saved games.

The original snapshot validator caps saved attempts at 99, although its live counter can exceed that and then produce an unrestorable link. The native pilot preserves full repeated-practice scoring and automatically upgrades only such overflow snapshots to native version 4. These extended snapshots resume in the native pilot; the older app cannot interpret them. Ordinary snapshots remain version 3. First-pass and valuation recheck scoring rules are unchanged.

## Build and tests

```bash
PY=/workspace/.cloud-setup/venvs/main/bin/python
"$PY" native-pilot/export.py
node --test native-pilot/tests/*.test.mjs
"$PY" -m unittest discover -s tests -v
"$PY" native-pilot/tests/browser.py
"$PY" native-pilot/build.py
```

Serve `native-pilot/dist/` over ordinary HTTP/HTTPS for a local preview. `file://` is unsupported. The actual browser tests use `/native-pilot/` subdirectory hosting, all external traffic blocked, fresh Chromium contexts, screenshots, table downloads and original Python snapshot validation. See `VALIDATION.md` and `review/` for evidence.

The build copies only the six approved native assets and writes their SHA-256 manifest. It does not publish. Publication appends this directory to the existing static branch after checking the current refs and proving that existing publishing files are byte-identical.

## Compatibility and measurements

This pilot requires a current browser supporting ES modules, BigInt, Web Crypto, structured cloning and Compression/Decompression Streams. Chromium is tested; physical-device and broader browser coverage are not yet measured. Compression Streams compress the small saved URL snapshot; there is no application-runtime download or package installation.

Cold initialization measurements use five cache-disabled fresh Chromium contexts on local loopback in the saved cloud environment. They are not hosted-network, school-device, school-bandwidth, or classroom-capacity measurements. They do not promise a specific real-world startup time.

Hosted browser testing remains unavailable because of the known cloud proxy restriction on the Pages hostname. Publication status and its URL are verified through GitHub's deployment evidence; no alternate access route is used. The preview is for pilot testing and does not replace the current student app.
