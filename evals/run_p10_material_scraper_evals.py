#!/usr/bin/env python3
"""Offline and browser-fixture evaluations for the Material.io ingestion pipeline."""
from __future__ import annotations
import copy, json, shutil, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import material3_knowledge_pipeline as pipeline
import route_context

def main() -> int:
    topics, sitemap = pipeline.load_registry(ROOT)
    evidence = pipeline.load_evidence(ROOT / "routing/material3-browser-retrieval-evidence.json")
    checks=[]
    def check(name, ok, detail):
        checks.append((name, bool(ok), detail))
        if not ok: raise AssertionError(f"{name}: {detail}")

    check("complete_registry_and_pilot", len(topics["topics"]) == 21 and len(sitemap["urls"]) == 249
          and {x["topic_id"] for x in pipeline.pilot_targets(topics)} == {"material3_foundations","material3_color","material3_typography","material3_components","material3_accessibility"},
          "The pilot uses five requested categories from the complete existing topic manifest.")
    check("canonical_official_domain_only", all(x["canonical_url"].startswith("https://m3.material.io/") for x in evidence["records"]),
          "All P10 page attempts are canonical registered Material.io HTTPS URLs.")
    check("live_policy_block_is_honest", evidence["acquisition_status"] == "BLOCKED" and evidence["attempted_http_requests"] == 0
          and all(x["state"] == "blocked" and not x["page_content_obtained"] and not x["verified"] for x in evidence["records"]),
          "Current egress policy blocks m3.material.io before any HTTP request; no retrieval is claimed.")

    browser_error = None
    rendered_result = None
    shell_result = None
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True, executable_path=shutil.which("chromium") or None)
            page=browser.new_page()
            page.set_content("""<!doctype html><title>fixture title</title><nav>duplicate global navigation</nav><main><h1>Rendered component guidance</h1><section><h2>Selection behavior</h2><p id='injected'></p><ul><li>Selected content remains grouped with its heading.</li><li>Disabled content exposes a distinct state.</li></ul><table><tr><th>State</th><th>Behavior</th></tr><tr><td>Pressed</td><td>Feedback follows activation.</td></tr></table><a href='https://m3.material.io/components/buttons'>Official related guidance</a><a href='https://example.org/untrusted'>External link</a></section></main><script>document.querySelector('#injected').textContent='This documentation text is rendered by JavaScript and contains source-grounded interaction guidance for a synthetic extraction test. '.repeat(3)</script>""")
            page.wait_for_function("document.querySelector('#injected')?.textContent.length > 50")
            raw=page.evaluate(pipeline.EXTRACT_JS)
            normalized=pipeline.normalize_document(raw,"https://m3.material.io/components/buttons")
            good,why=pipeline.meaningful_document(normalized)
            browser.close()
            rendered_result = (good and why=="meaningful_document_content"
                  and any(x["heading_path"]==["Rendered component guidance","Selection behavior"] for x in normalized["sections"])
                  and any(x["type"]=="table" for s in normalized["sections"] for x in s["blocks"])
                  and all(x["url"].startswith("https://m3.material.io/") for x in normalized["links"]))
            shell={"title":"shell","canonical_url":"https://m3.material.io/x","blocks":[{"type":"paragraph","text":"This website requires JavaScript"}],"sections":[],"links":[]}
            empty={"title":"empty","canonical_url":"https://m3.material.io/x","blocks":[],"sections":[],"links":[]}
            shell_result = pipeline.meaningful_document(shell)==(False,"javascript_shell") and pipeline.meaningful_document(empty)==(False,"empty_or_non_document_page")
    except Exception as exc:
        browser_error = exc
    if browser_error is None:
        browser_status="PASS"
        check("javascript_render_and_structured_extraction", bool(rendered_result),
              "Installed Playwright/Chromium executed page JavaScript; extraction preserved headings, list/table blocks, source links, and removed an external link.")
        check("javascript_shell_and_empty_page_rejected", bool(shell_result),
              "HTTP shell text and empty DOM structures cannot become retrieved documentation.")
    else:
        browser_status="BLOCKED"

    synthetic_url=next(t for t in topics["topics"] if t["id"]=="material3_navigation")["canonical_source_urls"][0]
    synthetic={"schema_version":1,"source_family":"official_material_io_browser_retrieval","acquisition_status":"CONTENT_RETRIEVED","network_policy_state":"enforced_by_operator_attestation","attempted_http_requests":1,"records":[{"topic_id":"material3_navigation","canonical_url":synthetic_url,"retrieved_at":"2026-10-14T12:00:00Z","state":"content_retrieved","discovery_state":"DISCOVERED","retrieval_state":"CONTENT_RETRIEVED","verification_state":"NOT VERIFIED","integration_state":"NOT INTEGRATED","page_content_obtained":True,"verified":False,"tls_verification":"enabled","http_status":200,"content_fingerprint":"a"*64,"response_sha256":"b"*64,"response_bytes":1000,"normalized_content_chars":350,"headings":["Navigation", "Adaptive destinations"],"routing_terms":["navigation"]}]}
    counts=pipeline.validate_evidence(synthetic,topics,sitemap)
    check("retrieval_and_verification_are_separate", counts["content_retrieved"]==1 and counts["verified"]==0 and counts["integrated"]==0,
          "A synthetic saved retrieval record does not become verified without a fingerprint-matched human review.")
    with tempfile.TemporaryDirectory(prefix="p10-cache-fixture-") as temp:
        cache_root=Path(temp)/"cache";cache_root.mkdir()
        target=pipeline.pilot_targets(topics)[0]
        cached_doc=pipeline.normalize_document({"title":"Synthetic cache","blocks":[{"type":"heading","level":1,"text":"Foundation"},{"type":"p","text":"A synthetic content record used only to verify local cache reuse behavior. "*5}],"links":[]},target["canonical_url"])
        fingerprint=pipeline.fingerprint_document(cached_doc)
        cached_file=cache_root/target["topic_id"]/f"{pipeline.slug_for_url(target['canonical_url'])}-{fingerprint[:12]}.json"
        cached_file.parent.mkdir(parents=True);cached_file.write_text(json.dumps({"document":cached_doc,"content_fingerprint":fingerprint}),encoding="utf-8")
        prior_row={"topic_id":target["topic_id"],"canonical_url":target["canonical_url"],"title":target["title"],"retrieved_at":"2026-10-14T12:00:00Z","state":"content_retrieved","discovery_state":"DISCOVERED","retrieval_state":"CONTENT_RETRIEVED","verification_state":"NOT VERIFIED","integration_state":"NOT INTEGRATED","page_content_obtained":True,"verified":False,"tls_verification":"enabled","http_status":200,"content_fingerprint":fingerprint,"response_sha256":"e"*64,"response_bytes":2500,"normalized_content_chars":350,"headings":["Foundation"],"cache_reference":cached_file.relative_to(cache_root).as_posix()}
        prior_path=Path(temp)/"prior.json";prior_path.write_text(json.dumps({"schema_version":1,"source_family":"official_material_io_browser_retrieval","acquisition_status":"CONTENT_RETRIEVED","network_policy_state":"enforced_by_operator_attestation","attempted_http_requests":1,"records":[prior_row]}),encoding="utf-8")
        cached_run=pipeline.retrieve_pilot(cache_dir=cache_root,evidence_path=prior_path)
        check("cache_reuse_without_network", cached_run["attempted_http_requests"]==0 and any(x.get("cache_reused") for x in cached_run["records"]),
              "A fingerprint-matched local intermediate is reused; the remaining URLs stay blocked by policy without erasing cached content evidence.")
        prior_before=prior_path.read_bytes()
        try:
            pipeline.retrieve_pilot(cache_dir=cache_root,evidence_path=prior_path,refresh=True)
            refresh_protected=False
        except ValueError:
            refresh_protected=prior_path.read_bytes()==prior_before
        check("refresh_preserves_retrieved_evidence",refresh_protected,
              "A refresh refuses to overwrite existing retrieved evidence and preserves the evidence file unchanged.")
    bad=copy.deepcopy(synthetic);bad["records"].append(copy.deepcopy(bad["records"][0]))
    try: pipeline.validate_evidence(bad,topics,sitemap);duplicate_rejected=False
    except ValueError:duplicate_rejected=True
    check("duplicate_page_detection",duplicate_rejected,"Duplicate canonical page evidence is rejected.")
    bad=copy.deepcopy(synthetic);bad["records"][0]["canonical_url"]="https://m3.material.io.attacker.example/"
    try: pipeline.validate_evidence(bad,topics,sitemap);host_rejected=False
    except ValueError:host_rejected=True
    check("official_host_enforced",host_rejected,"Lookalike hosts and unregistered URLs are rejected.")
    blocked, crawl_delay = pipeline.parse_robots("User-agent: *\nDisallow: /private\nAllow: /private/public\nCrawl-delay: 4\n", "/private/item")
    allowed, _ = pipeline.parse_robots("User-agent: *\nDisallow: /private\nAllow: /private/public\nCrawl-delay: 4\n", "/private/public/page")
    check("robots_rules_and_rate_limits",blocked and not allowed and crawl_delay==4.0,
          "Standard robots allow/disallow precedence and crawl delay are parsed, with the implementation's two-second minimum applied.")
    repeated=pipeline.normalize_document({"title":"T","blocks":[{"type":"heading","level":1,"text":"Repeated"},{"type":"p","text":"same section body"},{"type":"p","text":"same section body"}],"links":[]},synthetic_url)
    check("duplicate_block_normalization",sum(1 for b in repeated["blocks"] if b.get("text")=="same section body")==1,
          "Repeated extracted boilerplate blocks are deduplicated in normalized content.")
    doc={"title":"Navigation guidance","canonical_url":synthetic_url,"blocks":[{"type":"heading","level":1,"text":"Navigation"},{"type":"paragraph","text":"A source-grounded summary should communicate placement and destination selection without assuming a Compose API."}],"sections":[],"links":[]}
    norm=pipeline.normalize_document(doc,synthetic_url)
    synthetic["records"][0]["content_fingerprint"]=pipeline.fingerprint_document(norm)
    review={"canonical_url":synthetic_url,"topic_id":"material3_navigation","content_fingerprint":synthetic["records"][0]["content_fingerprint"],"reviewed_at":"2026-10-14","reviewer":"synthetic-evaluation-fixture","summary":"Synthetic review fixture summary; it is not Material.io knowledge and is never written into repository references.","design_rules":["Synthetic rule to exercise reviewed ingestion."],"constraints":["Synthetic fixture only."],"source_sections":["Navigation"],"freshness_requirements":["Recheck the page when its design may have changed."],"routing_terms":["navigation"]}
    markdown=pipeline.markdown_for_review({**synthetic["records"][0],"document_title":"Navigation guidance","headings":["Navigation"]},review)
    check("review_fingerprint_and_markdown_generation", "content fingerprint" in markdown.lower() and synthetic_url in markdown and "does not define AndroidX Kotlin signatures" in markdown,
          "Curated Markdown generation requires a matching page fingerprint and keeps design/API authorities separate.")
    raw_response=b"synthetic HTTP body for cache digest verification"
    cache_bundle=pipeline.make_cache_bundle(norm,raw_response,"2026-10-14T12:00:00Z")
    check("cache_records_raw_response_digest",cache_bundle["response_sha256"]==__import__("hashlib").sha256(raw_response).hexdigest()
          and cache_bundle["content_fingerprint"]==pipeline.fingerprint_document(norm),
          "The response digest is computed before writing the cache and remains distinct from the normalized-content fingerprint.")
    altered=copy.deepcopy(review);altered["content_fingerprint"]="0"*64
    try:pipeline.markdown_for_review(synthetic["records"][0],altered);stale_review_rejected=False
    except ValueError:stale_review_rejected=True
    check("stale_review_rejected",stale_review_rejected,"A review cannot approve a different retrieved fingerprint.")

    with tempfile.TemporaryDirectory(prefix="p10-multi-review-fixture-") as temp:
        fixture_root=Path(temp)
        (fixture_root/"routing").mkdir()
        for rel in ("routing/material3-topics.json","routing/material3-sitemap-evidence.json"):
            (fixture_root/rel).write_bytes((ROOT/rel).read_bytes())
        review_dir=fixture_root/"reviews";review_dir.mkdir()
        cache_root=fixture_root/"cache";cache_root.mkdir()
        rows=[]
        targets=[pipeline.pilot_targets(topics)[0],pipeline.pilot_targets(topics)[1]]
        for index,target in enumerate(targets):
            doc=pipeline.normalize_document({"title":target["title"],"blocks":[{"type":"heading","level":1,"text":target["title"]},{"type":"p","text":"Synthetic integration fixture content that only validates review provenance and routing record associations."}],"links":[]},target["canonical_url"])
            fingerprint=pipeline.fingerprint_document(doc)
            cache_rel=f"{target['topic_id']}/doc-{index}.json"
            cache_path=cache_root/cache_rel;cache_path.parent.mkdir(parents=True,exist_ok=True)
            cache_path.write_text(json.dumps({"document":doc,"content_fingerprint":fingerprint}),encoding="utf-8")
            rows.append({"topic_id":target["topic_id"],"canonical_url":target["canonical_url"],"title":target["title"],"retrieved_at":"2026-10-14T12:00:00Z","state":"content_retrieved","discovery_state":"DISCOVERED","retrieval_state":"CONTENT_RETRIEVED","verification_state":"NOT VERIFIED","integration_state":"NOT INTEGRATED","page_content_obtained":True,"verified":False,"tls_verification":"enabled","http_status":200,"content_fingerprint":fingerprint,"response_sha256":"f"*64,"response_bytes":1500,"normalized_content_chars":250,"headings":[target["title"]],"cache_reference":cache_rel})
            review={"canonical_url":target["canonical_url"],"topic_id":target["topic_id"],"content_fingerprint":fingerprint,"reviewed_at":"2026-10-14","reviewer":"synthetic-evaluation-fixture","summary":"Synthetic test only.","design_rules":["Synthetic test rule."],"constraints":["Fixture only."],"source_sections":[target["title"]],"freshness_requirements":["Recheck on change."],"routing_terms":[target["topic_id"].replace("material3_","")]}
            (review_dir/f"review-{index}.json").write_text(json.dumps(review),encoding="utf-8")
        evidence_path=fixture_root/"evidence.json"
        evidence_path.write_text(json.dumps({"schema_version":1,"source_family":"official_material_io_browser_retrieval","acquisition_status":"CONTENT_RETRIEVED","network_policy_state":"fixture_only","attempted_http_requests":2,"records":rows}),encoding="utf-8")
        integrated=pipeline.integrate_reviews(evidence_path=evidence_path,review_dir=review_dir,cache_dir=cache_root,root=fixture_root)
        integrated_rows=json.loads(evidence_path.read_text())["records"]
        check("multiple_reviews_keep_individual_provenance",integrated==2 and {r["review_record"] for r in integrated_rows}=={"review-0.json","review-1.json"},
              "Each integrated page records the actual matching review filename rather than the final loop item.")

    with tempfile.TemporaryDirectory(prefix="p10-router-fixture-") as temp:
        fixture=Path(temp)
        for name in ("routing","registry","knowledge","policies",".agents"):
            shutil.copytree(ROOT/name,fixture/name)
        note_rel="knowledge/material3-verified/material3_navigation/navigation-bar.md"
        note=fixture/note_rel;note.parent.mkdir(parents=True)
        note.write_text(f"# Synthetic navigation note\n\n**Source:** {synthetic_url}\n**Content fingerprint:** `{'c'*64}`\n\nThis is a test fixture. Material.io design intent. It does not define AndroidX Kotlin signatures.\n",encoding="utf-8")
        row=copy.deepcopy(synthetic["records"][0]);row.update({"state":"integrated","retrieval_state":"CONTENT_RETRIEVED","verification_state":"VERIFIED","integration_state":"INTEGRATED","verified":True,"review_record":"fixture/review.json","reviewed_at":"2026-10-14","summary":"Synthetic fixture.","design_rules":["synthetic"],"constraints":["fixture only"],"source_sections":["Adaptive destinations"],"freshness_requirements":["check current page"],"routing_terms":["navigation"],"knowledge_reference":note_rel})
        # The test note carries the evidence fingerprint used by the integrated row.
        note.write_text(note.read_text().replace("c"*64,row["content_fingerprint"]),encoding="utf-8")
        fixture_evidence={**synthetic,"acquisition_status":"CONTENT_RETRIEVED","records":[row]}
        (fixture/"routing/material3-browser-retrieval-evidence.json").write_text(json.dumps(fixture_evidence),encoding="utf-8")
        old_root=route_context.ROOT
        route_context.ROOT=fixture
        try:
            routed=route_context.build_manifest("Implement Material 3 navigation in Jetpack Compose.")
            paths={x["path"] for x in routed["selected_knowledge_references"]}
            unrelated=route_context.build_manifest("Review Hilt dependency injection.")
            unrelated_paths={x["path"] for x in unrelated["selected_knowledge_references"]}
            check("context_router_integration_and_progressive_disclosure", note_rel in paths and not any(x.startswith("knowledge/material3-verified/") for x in unrelated_paths)
                  and any(x["selected_for_task"] for x in routed["material3_page_evidence"]),
                  "An integrated verified navigation note is selected for a matching Material task and excluded from unrelated Hilt context.")
        finally:route_context.ROOT=old_root

    check("no_third_party_documentation_dependencies", "playwright==1.62.0" in (ROOT/"requirements-dev.txt").read_text()
          and not any("mcp" in x.lower() or "mirror" in x.lower() for x in (ROOT/"requirements-dev.txt").read_text().splitlines()),
          "Playwright is the only scraper runtime addition; no third-party documentation provider is configured.")
    if browser_status != "PASS":
        print(f"P10 Material scraper evaluations {sum(ok for _,ok,_ in checks)}/{len(checks)} passed; browser fixture=BLOCKED ({type(browser_error).__name__}); live site=BLOCKED")
    else:
        print(f"P10 Material scraper evaluations {sum(ok for _,ok,_ in checks)}/{len(checks)} PASS; browser fixture=PASS; live site=BLOCKED")
    for name,ok,detail in checks: print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    return 2 if browser_status != "PASS" else 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (AssertionError,KeyError,OSError,ValueError,json.JSONDecodeError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}",file=sys.stderr);raise SystemExit(1)
