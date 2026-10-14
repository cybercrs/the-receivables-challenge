"""Actual native browser lesson, legacy progress, layout, CSV and cold initialization QA."""

from __future__ import annotations

import json
import statistics
import sys
import threading
import time
import traceback
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from receivables_challenge import case_data as case, engine, progress  # noqa: E402

SITE = ROOT / "native-pilot"
OUT = SITE / "review"
GROUPS = [
    (case.CLAIM_DECISIONS, "Check the claim"),
    (case.CREDIT_DECISIONS, "Check the tradeoff"),
    (case.AGING_DECISIONS, "Check the interpretation"),
    (case.REPORTING_DECISIONS, "Check the reporting decision"),
    (case.MANAGEMENT_DECISIONS, "Check the management decision"),
]


def main():
    OUT.mkdir(exist_ok=True)
    result = {
        "checks": [],
        "console_errors": [],
        "page_errors": [],
        "external_requests": [],
        "cold_initializations": [],
    }

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path.startswith("/native-pilot/"):
                self.path = self.path[len("/native-pilot") :]
            super().do_GET()

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(Handler, directory=str(SITE))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f"http://127.0.0.1:{server.server_port}"
    url = origin + "/native-pilot/"

    def passed(name):
        result["checks"].append({"name": name, "status": "passed"})
        print("PASSED:", name, flush=True)

    def loaded(page):
        page.locator("html[data-ready=true][data-saving=false]").wait_for(timeout=15000)
        assert not page.locator("#save-error:not([hidden])").count()

    def state(page):
        loaded(page)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)
        saved = progress.decode_snapshot(query.get("progress", [None])[0])
        assert saved is not None, (
            "Native saved state must be accepted by the unchanged Python validator"
        )
        return saved, int(query["view"][0])

    def click(page, label):
        page.get_by_role("button", name=label, exact=True).click()
        loaded(page)

    def select(page, value, group=None):
        target = page.get_by_role("radio", name=value, exact=True)
        target.check()
        loaded(page)

    def review(page):
        expect(
            page.get_by_text(
                "Review only. Return to your current page to continue the activity.",
                exact=True,
            )
        ).to_be_visible()
        assert not page.get_by_role("radio").count()
        assert not page.locator("main input").count()
        expect(
            page.get_by_role("button", name="Start over", exact=True)
        ).to_be_disabled()
        assert not page.locator("main .primary").count()

    def layout(page, label):
        boxes = [
            page.get_by_role("button", name=label, exact=True).bounding_box()
            for label in ["Back", "Forward"]
        ]
        assert all(
            box and box["width"] == 44 and box["height"] == 44 for box in boxes
        ), boxes
        main = page.locator(".block-container").bounding_box()
        assert boxes[0]["x"] > main["x"] + main["width"] / 2
        assert abs(boxes[0]["y"] - boxes[1]["y"]) < 1
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        result.setdefault("layout", {})[label] = boxes

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            proxy={"server": "http://127.0.0.1:9", "bypass": "127.0.0.1,localhost"},
        )

        def watch(page):
            page.on("pageerror", lambda error: result["page_errors"].append(str(error)))
            page.on(
                "console",
                lambda message: result["console_errors"].append(message.text)
                if message.type == "error"
                else None,
            )
            page.on(
                "request",
                lambda request: result["external_requests"].append(request.url)
                if request.url.startswith("http") and not request.url.startswith(origin)
                else None,
            )
            return page

        context = browser.new_context(
            viewport={"width": 1280, "height": 900}, accept_downloads=True
        )
        page = watch(context.new_page())
        try:
            page.goto(url, wait_until="domcontentloaded")
            loaded(page)
            assert state(page)[1] == 0
            layout(page, "desktop")
            page.screenshot(path=str(OUT / "briefing-desktop.png"), full_page=True)
            passed(
                "Native initialization, anonymous Python-compatible progress, desktop navigation"
            )
            click(page, "Open the receivables file")
            first = case.CLAIM_DECISIONS[0]
            click(page, "Check the claim")
            expect(page.get_by_role("alert")).to_contain_text("Choose a response")
            expect(
                page.get_by_role("button", name="Forward", exact=True)
            ).to_be_disabled()
            wrong = next(option for option in first.options if option != first.correct)
            select(page, wrong)
            click(page, "Check the claim")
            failed = state(page)[0]
            assert failed["rc_attempts"][f"claim:{first.id}"] == 1
            expect(
                page.get_by_text(f"Best response: {first.correct}", exact=True)
            ).to_be_visible()
            click(page, "Check revised response")
            assert state(page)[0]["rc_attempts"][f"claim:{first.id}"] == 2
            page.reload(wait_until="domcontentloaded")
            loaded(page)
            assert state(page)[0]["rc_claim_responses"][first.id] == wrong
            select(page, first.correct)
            click(page, "Check revised response")
            saved = state(page)[0]
            assert saved["rc_attempts"][f"claim:{first.id}"] == 3
            assert saved["rc_first_pass"][f"claim:{first.id}"] is False
            expect(
                page.get_by_role("button", name="Forward", exact=True)
            ).to_be_disabled()
            for _ in range(3):
                click(page, "Back")
                review(page)
                assert state(page)[0] == saved
                click(page, "Forward")
                assert state(page)[0] == saved
            page.get_by_role("button", name="Continue", exact=True).focus()
            page.keyboard.press("Shift+Tab")
            back = page.get_by_role("button", name="Back", exact=True)
            # The native reset/navigation row retains ordinary keyboard order.
            back.focus()
            page.keyboard.press("Tab")
            page.keyboard.press("Shift+Tab")
            expect(back).to_be_focused()
            assert back.evaluate("e=>e.matches(':focus-visible')")
            assert back.evaluate("e=>getComputedStyle(e).outlineWidth") == "2px"
            page.keyboard.press("Enter")
            loaded(page)
            review(page)
            page.get_by_role("button", name="Forward", exact=True).focus()
            page.keyboard.press("Enter")
            loaded(page)
            assert state(page)[0] == saved
            passed(
                "Missing and repeated wrong answers, refresh, original reveal/revision scoring, immutable and keyboard review"
            )
            click(page, "Continue")
            second = case.CLAIM_DECISIONS[1]
            select(page, second.correct)
            draft = state(page)[0]
            order = page.get_by_role("radio").evaluate_all(
                "elements=>elements.map(e=>e.value)"
            )
            click(page, "Back")
            review(page)
            bookmark = page.url
            page.reload(wait_until="domcontentloaded")
            loaded(page)
            assert state(page)[0] == draft
            clone = watch(context.new_page())
            clone.goto(bookmark, wait_until="domcontentloaded")
            loaded(clone)
            review(clone)
            click(clone, "Forward")
            expect(
                clone.get_by_role("radio", name=second.correct, exact=True)
            ).to_be_checked()
            assert (
                clone.get_by_role("radio").evaluate_all(
                    "elements=>elements.map(e=>e.value)"
                )
                == order
            )
            clone.goto(
                clone.url.replace("view=2", "view=999"), wait_until="domcontentloaded"
            )
            loaded(clone)
            assert state(clone)[1] == 2
            expect(
                clone.get_by_role("button", name="Forward", exact=True)
            ).to_be_disabled()
            clone.close()
            click(page, "Forward")
            passed(
                "Unsubmitted drafts, exact stable option order, read-only bookmarks and future-view clamping"
            )
            for group_index, (items, check) in enumerate(GROUPS):
                if group_index == 3:
                    # Preserve both valid formatted amounts and invalid unfinished drafts in the URL.
                    page.locator("#widget_valuation_ending_allowance").fill("22,")
                    loaded(page)
                    page.reload(wait_until="domcontentloaded")
                    loaded(page)
                    expect(
                        page.locator("#widget_valuation_ending_allowance")
                    ).to_have_value("22,")
                    select(page, case.VALUATION_BENEFIT_CORRECT)
                    click(page, "Check the valuation")
                    expect(page.get_by_role("alert")).to_contain_text(
                        "whole-dollar amounts"
                    )
                    assert not state(page)[0]["rc_valuation_submitted"]
                    for key, _label in case.VALUATION_FIELDS:
                        page.locator(f"#widget_valuation_{key}").fill("0")
                        loaded(page)
                    click(page, "Check the valuation")
                    attempts = state(page)[0]["rc_attempts"]
                    click(page, "Check revised valuation")
                    assert state(page)[0]["rc_attempts"] == attempts
                    assert not page.get_by_role(
                        "button", name="Continue to reporting", exact=True
                    ).count()
                    for key, value in engine.valuation_values().items():
                        page.locator(f"#widget_valuation_{key}").fill(f"${value:,}")
                        loaded(page)
                    calculated_draft = state(page)[0]
                    page.reload(wait_until="domcontentloaded")
                    loaded(page)
                    assert state(page)[0] == calculated_draft
                    for key, value in engine.valuation_values().items():
                        expect(page.locator(f"#widget_valuation_{key}")).to_have_value(
                            f"${value:,}"
                        )
                    click(page, "Check revised valuation")
                    expect(
                        page.get_by_text("Method comparison:", exact=False)
                    ).to_contain_text("$9,440")
                    saved_table_state = state(page)[0]
                    page.get_by_role("table").get_by_role(
                        "button", name="Age category", exact=True
                    ).click()
                    expect(
                        page.get_by_role("table")
                        .locator("tbody tr")
                        .first.locator("td")
                        .first
                    ).to_have_text("1-30 days past due")
                    assert state(page)[0] == saved_table_state
                    page.get_by_role("table").get_by_role(
                        "button", name="Age category", exact=True
                    ).click()
                    expect(
                        page.get_by_role("table")
                        .locator("tbody tr")
                        .first.locator("td")
                        .first
                    ).to_have_text("More than 90 days past due")
                    assert state(page)[0] == saved_table_state
                    click(page, "Expand table")
                    expect(page.get_by_role("dialog")).to_be_visible()
                    assert state(page)[0] == saved_table_state
                    click(page, "Close table")
                    with page.expect_download() as download_event:
                        click(page, "Download table as CSV")
                    download = download_event.value
                    download.save_as(str(OUT / "valuation-table.csv"))
                    csv = (OUT / "valuation-table.csv").read_text()
                    assert "Age category" in csv and "More than 90 days past due" in csv
                    assert csv.count("\n") == 6 and "Total" not in csv
                    click(page, "Continue to reporting")
                    passed(
                        "Whole-dollar validation, invalid and formatted numeric draft resume, calculation gates, unchanged rechecks and table CSV"
                    )
                for index, item in enumerate(items):
                    if group_index == 0 and index == 0:
                        continue
                    select(page, item.correct)
                    click(page, check)
                    if item.id == "writeoff_accounts":
                        expect(page.get_by_text("$95,820", exact=True)).to_have_count(2)
                        expect(page.get_by_text("$104,000", exact=True)).to_be_visible()
                        page.screenshot(
                            path=str(OUT / "writeoff-desktop.png"), full_page=True
                        )
                    label = (
                        "Finish the case"
                        if group_index == 4 and index == len(items) - 1
                        else "Continue"
                    )
                    click(page, label)
                    if group_index == 2 and index == 0:
                        expect(page.get_by_role("table")).to_have_count(1)
                        # Original numbered cells and total remain visible in the aging screen.
                        expect(
                            page.get_by_text("[4] $22,180", exact=True)
                        ).to_be_visible()
            completed, view = state(page)
            assert view == 24 and completed["rc_stage"] == 7
            expected_score = {
                "correct": 22,
                "attempted": 27,
                "total": 27,
                "revisions": 6,
            }
            assert progress.score_summary(completed) == expected_score
            result["score"] = expected_score
            expect(
                page.get_by_text("Valuation first pass:", exact=False)
            ).to_contain_text("All first-pass decisions: 22 of 27")
            assert page.locator("details").count() == 4
            for details in page.locator("details").all():
                details.locator("summary").click()
                assert details.inner_text().strip()
            page.mouse.move(0, 0)
            page.screenshot(path=str(OUT / "complete-desktop.png"), full_page=True)
            passed(
                "Complete 25-page lesson, all 22 choices, original write-off balances, category scores and four debrief disclosures"
            )
            for position in range(23, -1, -1):
                click(page, "Back")
                review(page)
                assert state(page)[0] == completed and state(page)[1] == position
                if position == 12:
                    page.screenshot(
                        path=str(OUT / "review-desktop.png"), full_page=True
                    )
                    with page.expect_download() as event:
                        click(page, "Download table as CSV")
                    event.value.save_as(str(OUT / "review-table.csv"))
                    assert state(page)[0] == completed
            for position in range(1, 25):
                click(page, "Forward")
                assert state(page)[0] == completed and state(page)[1] == position
            page.set_viewport_size({"width": 390, "height": 844})
            layout(page, "narrow")
            page.mouse.move(0, 0)
            page.screenshot(path=str(OUT / "complete-narrow.png"), full_page=True)
            click(page, "Back")
            review(page)
            page.screenshot(path=str(OUT / "review-narrow.png"), full_page=True)
            click(page, "Forward")
            passed(
                "Full immutable backward/forward traversal, review-only CSV, narrow layout and usable touch targets"
            )
            fresh = watch(context.new_page())
            fresh.goto(url, wait_until="domcontentloaded")
            loaded(fresh)
            assert state(fresh)[1] == 0
            fresh.close()
            other_context = browser.new_context()
            other_page = watch(other_context.new_page())
            other_page.goto(url, wait_until="domcontentloaded")
            loaded(other_page)
            assert state(other_page)[1] == 0
            other_context.close()
            click(page, "Start over")
            assert state(page)[1] == 0 and not state(page)[0]["rc_claim_responses"]
            page.reload(wait_until="domcontentloaded")
            loaded(page)
            assert state(page)[1] == 0
            page.goto(url + "?progress=invalid&view=999", wait_until="domcontentloaded")
            loaded(page)
            assert state(page)[1] == 0
            # An actual original snapshot, with a seed beyond JS safe integers, remains interoperable.
            legacy = progress.activity_defaults()
            legacy["rc_stage"] = 1
            legacy["rc_shuffle_seed"] = 2**63 - 1
            legacy["rc_drafts"]["claims"][first.id] = wrong
            legacy_url = url + "?progress=" + progress.encode_state(legacy) + "&view=1"
            page.goto(legacy_url, wait_until="domcontentloaded")
            loaded(page)
            assert state(page)[0]["rc_shuffle_seed"] == 2**63 - 1
            expect(page.get_by_role("radio", name=wrong, exact=True)).to_be_checked()
            click(page, "Check the claim")
            assert state(page)[0]["rc_claim_responses"][first.id] == wrong
            passed(
                "Independent tabs and contexts, reset/refresh, invalid snapshot rejection, original 63-bit bookmark compatibility"
            )
            context.close()
            for _ in range(5):
                cold = browser.new_context(viewport={"width": 1280, "height": 900})
                cold_page = watch(cold.new_page())
                cdp = cold.new_cdp_session(cold_page)
                cdp.send("Network.enable")
                cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
                start = time.perf_counter()
                cold_page.goto(url, wait_until="domcontentloaded")
                loaded(cold_page)
                result["cold_initializations"].append(
                    {
                        "ready_from_navigation_ms": cold_page.evaluate(
                            "performance.getEntriesByName('receivables-ready')[0].startTime"
                        ),
                        "automation_wall_ms": (time.perf_counter() - start) * 1000,
                        "browser_resource_bytes": cold_page.evaluate(
                            "performance.getEntriesByType('resource').reduce((sum,r)=>sum+r.encodedBodySize,0)"
                        ),
                    }
                )
                cold.close()
            timings = [
                x["ready_from_navigation_ms"] for x in result["cold_initializations"]
            ]
            result["cold_summary_ms"] = {
                "median": statistics.median(timings),
                "min": min(timings),
                "max": max(timings),
            }
            result["measurement_scope"] = (
                "Five cache-disabled fresh Chromium contexts on local loopback in the saved cloud environment; not school-network, hosted HTTPS, device or classroom-load measurements."
            )
            delivered = [
                "index.html",
                "original.css",
                "style.css",
                "content.js",
                "engine.js",
                "app.js",
            ]
            result["package_bytes"] = {
                name: (SITE / name).stat().st_size for name in delivered
            }
            result["package_total_bytes"] = sum(result["package_bytes"].values())
            assert (
                not result["page_errors"]
                and not result["console_errors"]
                and not result["external_requests"]
            )
            passed(
                "Five measured cold native initializations; no runtime installation, external requests, console errors or execution errors"
            )
            result["status"] = "passed"
        except Exception:
            result["status"] = "failed"
            result["failure"] = traceback.format_exc()
            print(result["failure"], flush=True)
            if not page.is_closed():
                page.screenshot(path=str(OUT / "failure.png"), full_page=True)
        finally:
            (OUT / "browser-results.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            browser.close()
            server.shutdown()
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
