#!/usr/bin/env python3
"""Policy-gated browser retrieval and reviewed knowledge integration for m3.material.io.

Retrieved page bodies and normalized structures belong in a local cache. The
repository evidence file stores hashes and states, not full page copies. Content
is VERIFIED only after a human review record matches the retrieved fingerprint;
the router then selects the generated topic reference progressively.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_HOST = "m3.material.io"
OFFICIAL_ORIGINS = {"m3.material.io", "www.google.com", "fonts.googleapis.com", "fonts.gstatic.com", "www.gstatic.com"}
USER_AGENT = "Android-brain-Material3-KnowledgeBot/0.1 (public documentation retrieval; contact via repository issues)"
MAX_BODY_CHARS = 250_000
MIN_CONTENT_CHARS = 200


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_registry(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    topics = json.loads((root / "routing/material3-topics.json").read_text(encoding="utf-8"))
    sitemap = json.loads((root / "routing/material3-sitemap-evidence.json").read_text(encoding="utf-8"))
    urls = set(sitemap["urls"])
    if len(topics["topics"]) != 21 or len(urls) != 249:
        raise ValueError("P10 expects the existing 21 topic groups and 249 discovered URLs")
    for topic in topics["topics"]:
        if topic.get("classification") != "material_io_design_specification":
            raise ValueError(f"unexpected Material topic classification: {topic.get('id')}")
        if not set(topic.get("canonical_source_urls", [])) <= urls:
            raise ValueError(f"topic contains URLs outside the recorded sitemap: {topic.get('id')}")
    return topics, sitemap


def pilot_targets(topics_doc: dict[str, Any]) -> list[dict[str, str]]:
    wanted = ("material3_foundations", "material3_color", "material3_typography", "material3_components", "material3_accessibility")
    by_id = {x["id"]: x for x in topics_doc["topics"]}
    selected = []
    for topic_id in wanted:
        topic = by_id.get(topic_id)
        if topic is None:
            raise ValueError(f"pilot topic missing from established taxonomy: {topic_id}")
        urls = topic["canonical_source_urls"]
        canonical = topic.get("canonical_source_url")
        if canonical not in urls:
            canonical = urls[0]
        selected.append({"topic_id": topic_id, "canonical_url": canonical, "title": topic["title"]})
    return selected


def validate_target(url: str, registered_urls: set[str]) -> None:
    parsed = urlparse(url)
    if url not in registered_urls or parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST or parsed.username or parsed.password or parsed.port:
        raise ValueError(f"refusing noncanonical or unregistered Material.io URL: {url}")


def host_is_allowed(host: str, policy_path: Path = Path("/etc/codex/network-policy.json")) -> tuple[bool, str]:
    """Fail closed in managed environments unless the exact target is allowlisted."""
    if not policy_path.exists():
        return True, "no managed network-policy file; runtime egress enforcement remains external"
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))["http_network_policy"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return False, f"managed network policy unavailable or unreadable: {type(exc).__name__}"
    if policy.get("type") != "unrestricted":
        allowed = {row.get("host") for row in policy.get("egress_rules", [])}
        if host not in allowed:
            return False, f"{host} is absent from restricted HTTP egress rules"
    return True, "target appears in managed egress rules; caller must separately confirm policy is enforced"


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


EXTRACT_JS = r"""() => {
  const roots = [...document.querySelectorAll('main, article, [role="main"]')];
  const root = roots.sort((a,b) => (b.innerText || '').length - (a.innerText || '').length)[0] || document.body;
  const clone = root.cloneNode(true);
  clone.querySelectorAll('nav, header, footer, aside, script, style, noscript, [role="navigation"], [aria-modal="true"], [data-cookie-banner]').forEach(n => n.remove());
  const blocks = [];
  const sel = 'h1,h2,h3,h4,h5,h6,p,ul,ol,table,blockquote';
  for (const el of clone.querySelectorAll(sel)) {
    if (el.closest('ul,ol') && !['UL','OL'].includes(el.tagName)) continue;
    if (el.closest('table') && el.tagName !== 'TABLE') continue;
    const tag = el.tagName.toLowerCase();
    const text = (el.innerText || el.textContent || '').replace(/\s+/g,' ').trim();
    if (!text) continue;
    if (/^h[1-6]$/.test(tag)) blocks.push({type:'heading',level:Number(tag[1]),text});
    else if (tag === 'ul' || tag === 'ol') {
      const items = [...el.children].filter(x => x.tagName === 'LI').map(x => (x.innerText || x.textContent || '').replace(/\s+/g,' ').trim()).filter(Boolean);
      if (items.length) blocks.push({type:'list',ordered:tag==='ol',items});
    } else if (tag === 'table') {
      const rows = [...el.querySelectorAll('tr')].map(row => [...row.querySelectorAll('th,td')].map(cell => (cell.innerText || cell.textContent || '').replace(/\s+/g,' ').trim()));
      if (rows.length) blocks.push({type:'table',rows});
    } else blocks.push({type:tag,text});
  }
  const links = [...clone.querySelectorAll('a[href]')].map(a => ({text:(a.innerText||a.textContent||'').replace(/\s+/g,' ').trim(),url:new URL(a.href,location.href).href})).filter(x=>x.text);
  return {title:(document.querySelector('h1')?.innerText || document.title || '').replace(/\s+/g,' ').trim(), page_url:location.href, has_main:roots.length>0, blocks, links};
}"""


def document_text(doc: dict[str, Any]) -> str:
    out = []
    for block in doc.get("blocks", []):
        if block.get("type") == "list":
            out.extend(block.get("items", []))
        elif block.get("type") == "table":
            out.extend(" | ".join(row) for row in block.get("rows", []))
        elif block.get("text"):
            out.append(block["text"])
    return normalize_text(" ".join(out))


def normalize_document(doc: dict[str, Any], canonical_url: str) -> dict[str, Any]:
    """Normalize blocks, retain heading ancestry, and deduplicate repeated text."""
    stack: list[tuple[int, str]] = []
    sections: list[dict[str, Any]] = []
    normalized_blocks: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, ...], str]] = set()
    for block in doc.get("blocks", []):
        if block.get("type") == "heading":
            level = int(block.get("level", 1))
            title = normalize_text(block.get("text", ""))
            stack = [(n, t) for n, t in stack if n < level]
            stack.append((level, title))
            seen.clear()
            sections.append({"source_url": canonical_url, "heading_path": [t for _, t in stack], "blocks": []})
            normalized_blocks.append({"type": "heading", "level": level, "text": title})
            continue
        normalized = dict(block)
        if "text" in normalized: normalized["text"] = normalize_text(normalized["text"])
        if "items" in normalized: normalized["items"] = [normalize_text(x) for x in normalized["items"]]
        if "rows" in normalized: normalized["rows"] = [[normalize_text(cell) for cell in row] for row in normalized["rows"]]
        key = (tuple(t for _, t in stack), json.dumps(normalized, sort_keys=True, ensure_ascii=False))
        if key in seen: continue
        seen.add(key)
        normalized_blocks.append(normalized)
        if not sections:
            sections.append({"source_url": canonical_url, "heading_path": [], "blocks": []})
        sections[-1]["blocks"].append(normalized)
    links = []
    link_seen = set()
    for link in doc.get("links", []):
        url = link.get("url", "")
        text = normalize_text(link.get("text", ""))
        parsed = urlparse(url)
        if text and url and parsed.scheme == "https" and parsed.hostname in {OFFICIAL_HOST, "developer.android.com", "github.com"} and (text, url) not in link_seen:
            links.append({"text": text, "url": url, "source_url": canonical_url})
            link_seen.add((text, url))
    return {"title": normalize_text(doc.get("title", "")), "canonical_url": canonical_url, "blocks": normalized_blocks, "sections": sections, "links": links}


def meaningful_document(doc: dict[str, Any]) -> tuple[bool, str]:
    text = document_text(doc)
    headings = [b for b in doc.get("blocks", []) if b.get("type") == "heading"]
    low = text.casefold()
    if "this website requires javascript" in low or "enable javascript to run this app" in low:
        return False, "javascript_shell"
    if len(text) < MIN_CONTENT_CHARS or not headings:
        return False, "empty_or_non_document_page"
    return True, "meaningful_document_content"


def fingerprint_document(doc: dict[str, Any]) -> str:
    normalized = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_cache_bundle(doc: dict[str, Any], raw_response: bytes, retrieved_at: str) -> dict[str, Any]:
    """Keep the raw response digest and normalized-document fingerprint distinct."""
    return {
        "document": doc,
        "response_sha256": hashlib.sha256(raw_response).hexdigest(),
        "content_fingerprint": fingerprint_document(doc),
        "retrieved_at": retrieved_at,
    }


def slug_for_url(url: str) -> str:
    tail = urlparse(url).path.strip("/").split("/")[-1] or "overview"
    return re.sub(r"[^a-z0-9]+", "-", tail.lower()).strip("-")[:72]


def parse_robots(body: str, path: str, user_agent: str = "Android-brain-Material3-KnowledgeBot") -> tuple[bool, float]:
    groups: list[tuple[list[str], list[tuple[str, str]]]] = []
    agents: list[str] = []
    rules: list[tuple[str, str]] = []
    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line: continue
        key, value = (x.strip() for x in line.split(":", 1))
        key = key.casefold()
        if key == "user-agent":
            if rules:
                groups.append((agents, rules)); agents=[];rules=[]
            agents.append(value.casefold())
        elif agents and key in {"allow", "disallow", "crawl-delay"}:
            rules.append((key, value))
    if agents: groups.append((agents, rules))
    ua = user_agent.casefold()
    matched = [(a, r) for a, r in groups if any(token == "*" or token in ua for token in a)]
    specificity = max((len(token) for agents_, _ in matched for token in agents_ if token != "*" and token in ua), default=0)
    chosen = [(a, r) for a, r in matched if "*" in a] if specificity == 0 else [(a, r) for a, r in matched if any(len(token)==specificity and token in ua for token in a)]
    relevant = [item for _, group_rules in chosen for item in group_rules]
    matching_rules: list[tuple[int, bool]] = []
    for kind, pattern in relevant:
        if kind not in {"allow", "disallow"} or not pattern: continue
        expression = "^" + "".join(".*" if char == "*" else re.escape(char) for char in pattern.rstrip("$"))
        if pattern.endswith("$"): expression += "$"
        if re.search(expression, path):
            matching_rules.append((len(pattern.replace("*", "").rstrip("$")), kind == "allow"))
    denied = bool(matching_rules) and not max(matching_rules, key=lambda item: (item[0], item[1]))[1]
    delays = []
    for kind, value in relevant:
        if kind == "crawl-delay":
            try: delays.append(float(value))
            except ValueError: pass
    delay = max(delays, default=2.0)
    return denied, min(30.0, max(2.0, delay))


def blocked_record(target: dict[str, str], reason: str) -> dict[str, Any]:
    return {**target, "retrieved_at": now_utc(), "state": "blocked", "discovery_state": "DISCOVERED", "retrieval_state": "BLOCKED", "verification_state": "NOT VERIFIED", "integration_state": "NOT INTEGRATED", "page_content_obtained": False, "verified": False, "block_reason": reason, "retrieval_method": "not_attempted_network_policy_gate", "tls_verification": "enabled_no_request_made"}


def retrieve_pilot(*, root: Path = ROOT, cache_dir: Path, evidence_path: Path | None = None, refresh: bool = False, network_policy_enforced: bool = False, delay_seconds: float = 2.0, retries: int = 2) -> dict[str, Any]:
    topics_doc, sitemap = load_registry(root)
    url_set = set(sitemap["urls"])
    targets = pilot_targets(topics_doc)
    for target in targets: validate_target(target["canonical_url"], url_set)
    cache_root = cache_dir.resolve()
    prior_by_url: dict[str, dict[str, Any]] = {}
    if evidence_path and evidence_path.is_file():
        prior = load_evidence(evidence_path)
        validate_evidence(prior, topics_doc, sitemap, root=root)
        prior_by_url = {x["canonical_url"]: x for x in prior["records"] if x.get("state") in {"content_retrieved", "verified", "integrated"}}
    if refresh and prior_by_url:
        raise ValueError("refusing to refresh an evidence file with prior retrieved content in place; use a new --evidence output and re-review before replacing existing knowledge")
    records: list[dict[str, Any]] = []
    pending: list[dict[str, str]] = []
    for target in targets:
        prior_row = prior_by_url.get(target["canonical_url"])
        if prior_row and prior_row.get("cache_reference"):
            cache_path = (cache_root / prior_row["cache_reference"]).resolve()
            try:
                cache_path.relative_to(cache_root)
                bundle = json.loads(cache_path.read_text(encoding="utf-8"))
                doc = bundle["document"]
                if fingerprint_document(doc) == prior_row["content_fingerprint"]:
                    records.append({**prior_row, "cache_reused": True, "cache_reference": cache_path.relative_to(cache_root).as_posix()})
                    continue
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                if prior_row:
                    records.append({**prior_row, "refresh_status": "cache_unavailable_previous_retrieval_record_preserved"})
                    continue
        pending.append(target)
    if not pending:
        return {"schema_version": 1, "collection_started_at": now_utc(), "source_family": "official_material_io_browser_retrieval", "acquisition_status": "CONTENT_RETRIEVED", "network_policy_state": "cache_reuse_no_network", "attempted_http_requests": 0, "records": sorted(records, key=lambda x: x["canonical_url"])}
    allowed, reason = host_is_allowed(OFFICIAL_HOST)
    if not allowed:
        records.extend(blocked_record(x, reason) for x in pending)
        return {"schema_version": 1, "collection_started_at": now_utc(), "source_family": "official_material_io_browser_retrieval", "acquisition_status": "BLOCKED", "network_policy_state": "target_not_allowlisted", "attempted_http_requests": 0, "records": sorted(records, key=lambda x: x["canonical_url"])}
    if not network_policy_enforced:
        records.extend(blocked_record(x, "managed network policy enforcement was not confirmed; no request made") for x in pending)
        return {"schema_version": 1, "collection_started_at": now_utc(), "source_family": "official_material_io_browser_retrieval", "acquisition_status": "BLOCKED", "network_policy_state": "enforcement_not_confirmed", "attempted_http_requests": 0, "records": sorted(records, key=lambda x: x["canonical_url"])}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        records.extend(blocked_record(x, "Playwright is not installed") for x in pending)
        return {"schema_version": 1, "collection_started_at": now_utc(), "source_family": "official_material_io_browser_retrieval", "acquisition_status": "BLOCKED", "network_policy_state": "allowed", "attempted_http_requests": 0, "records": sorted(records, key=lambda x: x["canonical_url"])}
    cache_dir.mkdir(parents=True, exist_ok=True)
    robots_cache: tuple[str, float] | None = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, ignore_https_errors=False, java_script_enabled=True)
        context.set_default_timeout(20_000)
        for target in pending:
            url = target["canonical_url"]
            page = context.new_page()
            def guard(route):
                parsed = urlparse(route.request.url)
                host = parsed.hostname or ""
                approved = host in OFFICIAL_ORIGINS or host == OFFICIAL_HOST or host.endswith(".google.com") or host.endswith(".googleapis.com") or host.endswith(".gstatic.com")
                if parsed.scheme in {"data", "blob", "about"} or approved:
                    route.continue_()
                else:
                    route.abort("blockedbyclient")
            page.route("**/*", guard)
            record: dict[str, Any] = {**target, "retrieved_at": now_utc(), "discovery_state": "DISCOVERED", "retrieval_state": "PENDING", "verification_state": "NOT VERIFIED", "integration_state": "NOT INTEGRATED", "retrieval_method": "Playwright Chromium rendered page; TLS verification enabled", "tls_verification": "enabled", "verified": False}
            try:
                if robots_cache is None:
                    response = context.request.get(f"https://{OFFICIAL_HOST}/robots.txt", timeout=15_000, headers={"User-Agent": USER_AGENT})
                    if response.url and urlparse(response.url).hostname != OFFICIAL_HOST:
                        raise RuntimeError("robots.txt redirected outside official host")
                    if response.status not in (200, 404):
                        raise RuntimeError(f"robots.txt unavailable with HTTP {response.status}; refusing to assume crawl permission")
                    robots_cache = (response.text() if response.status == 200 else "", delay_seconds)
                robots, crawl_delay = parse_robots(robots_cache[0], urlparse(url).path)
                if robots:
                    records.append({**record, "state": "blocked", "retrieval_state": "BLOCKED_BY_ROBOTS", "page_content_obtained": False, "block_reason": "robots.txt disallows this path", "http_status": None})
                    page.close(); continue
                response = None
                for attempt in range(retries + 1):
                    try:
                        response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                        page.wait_for_timeout(500)
                        try:
                            page.wait_for_function("""() => { const r=[...document.querySelectorAll('main,article,[role=main]')].sort((a,b)=>(b.innerText||'').length-(a.innerText||'').length)[0]; return document.readyState==='complete' && ((r?.innerText||'').trim().length>200 || (document.body?.innerText||'').trim().length>200); }""", timeout=8_000)
                        except Exception:
                            # Allow shell/empty detection to classify the rendered page below.
                            pass
                        break
                    except Exception:
                        if attempt >= retries: raise
                        page.wait_for_timeout(min(5000, 750 * (2 ** attempt)))
                final_url = page.url
                if urlparse(final_url).hostname != OFFICIAL_HOST or urlparse(final_url).scheme != "https":
                    raise RuntimeError("page redirected outside the canonical official HTTPS host")
                doc = normalize_document(page.evaluate(EXTRACT_JS), url)
                rendered_chars = len(document_text(doc))
                record.update({"http_status": response.status if response else None, "final_url": final_url, "document_title": doc.get("title", ""), "normalized_content_chars": rendered_chars})
                if rendered_chars > MAX_BODY_CHARS:
                    records.append({**record, "state": "blocked", "retrieval_state": "BLOCKED_SIZE_LIMIT", "page_content_obtained": False, "block_reason": "normalized document exceeded the configured extraction size limit"})
                    page.close(); continue
                good, reason = meaningful_document(doc)
                if not response or response.status != 200:
                    record.update({"state": "blocked", "retrieval_state": "BLOCKED_HTTP", "page_content_obtained": False, "block_reason": f"HTTP status {record['http_status']}"})
                elif not good:
                    record.update({"state": "retrieved_shell" if reason == "javascript_shell" else "empty_or_non_document", "retrieval_state": "SHELL_ONLY" if reason == "javascript_shell" else "EMPTY_OR_NON_DOCUMENT", "page_content_obtained": False, "block_reason": reason})
                else:
                    fingerprint = fingerprint_document(doc)
                    raw_response = response.body()
                    cache_path = cache_dir / target["topic_id"] / f"{slug_for_url(url)}-{fingerprint[:12]}.json"
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_bundle = make_cache_bundle(doc, raw_response, record["retrieved_at"])
                    cache_path.write_text(json.dumps(cache_bundle, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    record.update({"state": "content_retrieved", "retrieval_state": "CONTENT_RETRIEVED", "page_content_obtained": True, "content_fingerprint": fingerprint, "response_sha256": cache_bundle["response_sha256"], "response_bytes": len(raw_response), "cache_reference": cache_path.relative_to(cache_root).as_posix(), "normalized_content_chars": rendered_chars, "section_count": len(doc["blocks"]), "headings": [b["text"] for b in doc["blocks"] if b["type"] == "heading"]})
                records.append(record)
                page.wait_for_timeout(int(max(delay_seconds, crawl_delay) * 1000))
            except Exception as exc:
                records.append({**record, "state": "blocked", "retrieval_state": "BLOCKED_ERROR", "page_content_obtained": False, "block_reason": f"{type(exc).__name__}: {str(exc)[:300]}", "http_status": None})
            finally:
                page.close()
        context.close(); browser.close()
    states = {x["state"] for x in records}
    overall = "CONTENT_RETRIEVED" if "content_retrieved" in states else "BLOCKED" if "blocked" in states else "NOT VERIFIED"
    return {"schema_version": 1, "collection_started_at": now_utc(), "source_family": "official_material_io_browser_retrieval", "acquisition_status": overall, "network_policy_state": "enforced_by_operator_attestation", "attempted_http_requests": sum(1 for x in records if x.get("http_status") is not None and not x.get("cache_reused")), "records": sorted(records, key=lambda x: x["canonical_url"])}


def load_evidence(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("source_family") != "official_material_io_browser_retrieval":
        raise ValueError("unsupported P10 evidence schema or source family")
    return data


def validate_evidence(data: dict[str, Any], topics_doc: dict[str, Any], sitemap: dict[str, Any], *, require_integrated: bool = False, root: Path = ROOT) -> dict[str, int]:
    topic_map = {x["id"]: x for x in topics_doc["topics"]}
    urls = set(sitemap["urls"])
    seen: set[str] = set()
    counts = {x: 0 for x in ("blocked", "retrieved_shell", "empty_or_non_document", "content_retrieved", "verified", "integrated")}
    for row in data.get("records", []):
        topic = row.get("topic_id"); url = row.get("canonical_url"); state = row.get("state")
        if topic not in topic_map or url not in urls or url not in topic_map[topic]["canonical_source_urls"]:
            raise ValueError("evidence URL/topic provenance does not resolve to the official registry")
        validate_target(url, urls)
        if url in seen: raise ValueError(f"duplicate Material.io page evidence: {url}")
        seen.add(url)
        retrieved_date = datetime.fromisoformat(row["retrieved_at"].replace("Z", "+00:00"))
        if retrieved_date.date() > datetime.now(timezone.utc).date(): raise ValueError("retrieval timestamp is in the future")
        if state not in counts: raise ValueError(f"unsupported page state: {state}")
        counts[state] += 1
        state_contract = {"blocked": ("BLOCKED", "NOT VERIFIED", "NOT INTEGRATED"), "retrieved_shell": ("SHELL_ONLY", "NOT VERIFIED", "NOT INTEGRATED"), "empty_or_non_document": ("EMPTY_OR_NON_DOCUMENT", "NOT VERIFIED", "NOT INTEGRATED"), "content_retrieved": ("CONTENT_RETRIEVED", "NOT VERIFIED", "NOT INTEGRATED"), "verified": ("CONTENT_RETRIEVED", "VERIFIED", "NOT INTEGRATED"), "integrated": ("CONTENT_RETRIEVED", "VERIFIED", "INTEGRATED")}
        expected = state_contract[state]
        actual = (row.get("retrieval_state"), row.get("verification_state"), row.get("integration_state"))
        if actual != expected and not (state == "blocked" and str(actual[0]).startswith("BLOCKED_")):
            raise ValueError(f"retrieval/verification/integration state chain is inconsistent for {url}: state={state}, actual={actual}, expected={expected}")
        if row.get("discovery_state") != "DISCOVERED":
            raise ValueError(f"registered page does not have discovery evidence: {url}")
        if row.get("verified") is True and state not in {"verified", "integrated"}:
            raise ValueError("page verification contradicts retrieval state")
        if state in {"retrieved_shell", "empty_or_non_document", "blocked"} and (row.get("page_content_obtained") or row.get("verified")):
            raise ValueError("shell/empty/blocked state cannot claim content or verification")
        if state in {"content_retrieved", "verified", "integrated"}:
            if row.get("http_status") != 200 or row.get("page_content_obtained") is not True or row.get("tls_verification") != "enabled":
                raise ValueError("retrieved content lacks successful actual browser/TLS evidence")
            if not re.fullmatch(r"[a-f0-9]{64}", row.get("content_fingerprint", "")) or int(row.get("normalized_content_chars", 0)) < MIN_CONTENT_CHARS or not row.get("headings"):
                raise ValueError("retrieved content lacks a fingerprint, substantive text, or headings")
            if not re.fullmatch(r"[a-f0-9]{64}", row.get("response_sha256", "")) or int(row.get("response_bytes", 0)) <= 0:
                raise ValueError("retrieved content lacks raw response integrity evidence")
        if state in {"verified", "integrated"}:
            if not row.get("review_record") or not row.get("summary") or not row.get("design_rules") or not row.get("reviewed_at") or not row.get("routing_terms") or not row.get("freshness_requirements") or not row.get("source_sections"):
                raise ValueError("VERIFIED requires a matching review record and authored summary/rules")
            reviewed_date = datetime.fromisoformat(row["reviewed_at"])
            if reviewed_date.date() > datetime.now(timezone.utc).date(): raise ValueError("review date is in the future")
            if not set(row["source_sections"]) <= set(row.get("headings", [])):
                raise ValueError("review source headings do not match the retrieved document")
        if state == "integrated" and not row.get("knowledge_reference"):
            raise ValueError("INTEGRATED requires a generated local knowledge reference")
        if state == "integrated":
            ref = (root / row["knowledge_reference"]).resolve()
            if not ref.is_relative_to(root.resolve()) or not ref.is_file():
                raise ValueError("INTEGRATED knowledge reference is missing or escapes the repository")
            note = ref.read_text(encoding="utf-8")
            if url not in note or row["content_fingerprint"] not in note or "Material.io design intent" not in note:
                raise ValueError("INTEGRATED knowledge lacks matching URL, fingerprint, or design/API boundary")
        if state == "blocked" and (row.get("page_content_obtained") or row.get("verified")):
            raise ValueError("blocked retrieval cannot claim page content or verification")
    if require_integrated and not counts["integrated"]:
        raise ValueError("no Material.io knowledge is integrated")
    return counts


def markdown_for_review(row: dict[str, Any], review: dict[str, Any]) -> str:
    if review.get("content_fingerprint") != row.get("content_fingerprint") or review.get("canonical_url") != row.get("canonical_url") or review.get("topic_id") != row.get("topic_id"):
        raise ValueError("review record does not match the retrieved source fingerprint/topic/URL")
    required = ("reviewed_at", "reviewer", "summary", "design_rules", "constraints", "source_sections", "freshness_requirements")
    if any(not review.get(key) for key in required):
        raise ValueError("review record lacks required human-authored evidence fields")
    if not isinstance(review["design_rules"], list) or not isinstance(review["constraints"], list) or not isinstance(review["source_sections"], list):
        raise ValueError("review lists have invalid types")
    if not isinstance(review.get("routing_terms"), list) or not review["routing_terms"]:
        raise ValueError("review record needs task routing terms for progressive disclosure")
    if not set(review["source_sections"]) <= set(row.get("headings", [])):
        raise ValueError("review cites headings absent from the retrieved page structure")
    lines = [f"# {row.get('document_title') or row.get('title')}", "", f"**Topic:** `{row['topic_id']}`  ", f"**Source:** [{row['canonical_url']}]({row['canonical_url']})  ", f"**Retrieved:** {row['retrieved_at']}  ", f"**Reviewed:** {review['reviewed_at']} by {review['reviewer']}  ", f"**Content fingerprint:** `{row['content_fingerprint']}`", "", "## Engineering summary", "", review["summary"], "", "## Design rules supported by this source", ""]
    lines.extend(f"- {item}" for item in review["design_rules"])
    lines += ["", "## Constraints and limitations", ""]
    lines.extend(f"- {item}" for item in review["constraints"])
    lines += ["", "## Inspected source sections", ""]
    lines.extend(f"- {item}" for item in review["source_sections"])
    lines += ["", "## Implementation boundary", "", "This document records Material.io design intent. It does not define AndroidX Kotlin signatures, artifact versions, or experimental opt-ins. Verify those separately against the target project's official AndroidX dependencies.", "", "## Freshness", ""]
    lines.extend(f"- {item}" for item in review["freshness_requirements"])
    return "\n".join(lines) + "\n"


def integrate_reviews(*, evidence_path: Path, review_dir: Path, cache_dir: Path = Path(".cache/material3-scraper"), root: Path = ROOT) -> int:
    topics_doc, sitemap = load_registry(root)
    evidence = load_evidence(evidence_path)
    validate_evidence(evidence, topics_doc, sitemap, root=root)
    by_url = {x["canonical_url"]: x for x in evidence["records"]}
    integrated = 0
    prepared: list[tuple[dict[str, Any], dict[str, Any], str, Path, Path, str]] = []
    for review_path in sorted(review_dir.glob("*.json")):
        review = json.loads(review_path.read_text(encoding="utf-8"))
        row = by_url.get(review.get("canonical_url"))
        if not row or row["state"] != "content_retrieved":
            raise ValueError(f"review has no matching content-retrieved record: {review_path.name}")
        cache_root = cache_dir.resolve()
        cache_path = (cache_root / row.get("cache_reference", "")).resolve()
        try: cache_path.relative_to(cache_root)
        except ValueError as exc: raise ValueError("cache reference escapes the configured cache directory") from exc
        if not cache_path.is_file():
            raise ValueError(f"normalized retrieved document is unavailable for review: {review_path.name}")
        bundle = json.loads(cache_path.read_text(encoding="utf-8"))
        if bundle.get("document", {}).get("canonical_url") != row["canonical_url"] or fingerprint_document(bundle.get("document", {})) != row["content_fingerprint"]:
            raise ValueError(f"cached document does not match retrieval evidence: {review_path.name}")
        markdown = markdown_for_review(row, review)
        output_rel = Path("knowledge/material3-verified") / row["topic_id"] / f"{slug_for_url(row['canonical_url'])}.md"
        output = root / output_rel
        prepared.append((row, review, review_path.name, output_rel, output, markdown))
    for row, review, review_name, output_rel, output, markdown in prepared:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        row.update({"state": "integrated", "retrieval_state": "CONTENT_RETRIEVED", "verification_state": "VERIFIED", "verified": True, "review_record": review_name, "reviewed_at": review["reviewed_at"], "summary": review["summary"], "design_rules": review["design_rules"], "constraints": review["constraints"], "source_sections": review["source_sections"], "freshness_requirements": review["freshness_requirements"], "routing_terms": review["routing_terms"], "knowledge_reference": output_rel.as_posix(), "integration_state": "INTEGRATED"})
        integrated += 1
    evidence["records"] = sorted(evidence["records"], key=lambda x: (x["topic_id"], x["canonical_url"]))
    validate_evidence(evidence, topics_doc, sitemap, root=root)
    temp_path = evidence_path.with_suffix(evidence_path.suffix + ".tmp")
    temp_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(evidence_path)
    return integrated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pilot = sub.add_parser("pilot", help="retrieve one representative page for each of five pilot topics")
    pilot.add_argument("--cache-dir", type=Path, default=Path(".cache/material3-scraper"))
    pilot.add_argument("--evidence", type=Path, default=Path("routing/material3-browser-retrieval-evidence.json"))
    pilot.add_argument("--network-policy-enforced", action="store_true", help="operator attestation based on current cloud environment_status; never bypasses the target allowlist")
    pilot.add_argument("--refresh", action="store_true", help="ignore cached page structures and retrieve again")
    pilot.add_argument("--delay-seconds", type=float, default=2.0)
    pilot.add_argument("--retries", type=int, default=2)
    ingest = sub.add_parser("integrate", help="generate curated notes from fingerprint-matched human review JSON files")
    ingest.add_argument("--evidence", type=Path, default=Path("routing/material3-browser-retrieval-evidence.json"))
    ingest.add_argument("--review-dir", type=Path, required=True)
    ingest.add_argument("--cache-dir", type=Path, default=Path(".cache/material3-scraper"))
    a = parser.parse_args()
    try:
        if a.command == "pilot":
            result = retrieve_pilot(cache_dir=a.cache_dir, evidence_path=a.evidence, refresh=a.refresh, network_policy_enforced=a.network_policy_enforced, delay_seconds=max(2.0, min(60.0, a.delay_seconds)), retries=max(0, min(2, a.retries)))
            a.evidence.parent.mkdir(parents=True, exist_ok=True)
            a.evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"acquisition_status": result["acquisition_status"], "attempted_http_requests": result["attempted_http_requests"], "records": [{"topic_id": x["topic_id"], "url": x["canonical_url"], "state": x["state"], "block_reason": x.get("block_reason")} for x in result["records"]]}, ensure_ascii=False, indent=2))
            return 0 if result["acquisition_status"] in {"BLOCKED", "CONTENT_RETRIEVED"} else 2
        count = integrate_reviews(evidence_path=a.evidence, review_dir=a.review_dir, cache_dir=a.cache_dir)
        print(f"Integrated {count} human-reviewed Material.io page(s).")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"material3_knowledge_pipeline: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
