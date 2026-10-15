#!/usr/bin/env python3
"""Deterministically recommend task-scoped context from the local harness registry.

This is a transparent keyword router, not a semantic model or Codex skill activator.
It never fetches external URLs and it never claims selected files were read by Codex.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ROUTER_VERSION = "1.1.0"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    chars = [c if c.isalnum() else " " for c in value]
    return " ".join("".join(chars).split())


def compact(value: str) -> str:
    return "".join(c for c in normalized(value) if c.isalnum())


def match_term(task_normalized: str, task_compact: str, term: str) -> str | None:
    term_normalized = normalized(term)
    if not term_normalized:
        return None
    if re.search(rf"(?<!\w){re.escape(term_normalized)}(?!\w)", task_normalized):
        return "phrase"
    term_compact = compact(term)
    if len(term_compact) >= 6 and term_compact in task_compact:
        return "technical_identifier"
    return None


def term_is_negated(task_normalized: str, term: str) -> bool:
    """Recognize a small, documented set of explicit English negators."""
    phrase = normalized(term)
    if not phrase:
        return False
    pattern = rf"\b(?:do not|don t|dont|avoid|never|without|exclude|excluding|not use)\b(?:\s+\w+){{0,2}}\s+{re.escape(phrase)}\b"
    return re.search(pattern, task_normalized) is not None


def safe_path(relative: str) -> Path:
    resolved = (ROOT / relative).resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError(f"path escapes repository root: {relative}")
    return resolved


def authority_rank(source: dict[str, Any]) -> tuple[int, str]:
    level = source.get("authority_level", "")
    ranks = {
        "official_api_contract": 0,
        "official_implementation_guidance": 1,
        "official_design_guidance": 2,
        "first_party_guidance": 3,
        "official_open_source_example": 4,
        "first_party_design_tool": 5,
        "community_tool": 6,
        "community_design_reference": 7,
        "legacy_view_system_reference": 8,
        "official_legacy_view_implementation": 8,
    }
    return (ranks.get(level, 50), source["id"])


def build_manifest(task: str, *, as_of: date | None = None, budget_chars: int | None = None, project_config: dict[str, Any] | None = None, project_config_path: str | None = None) -> dict[str, Any]:
    if not task.strip():
        raise ValueError("task must not be empty")
    taxonomy = load_json(ROOT / "routing/task-taxonomy.json")
    sources_doc = load_json(ROOT / "registry/sources.json")
    skills_doc = load_json(ROOT / "registry/skills.json")
    policies_doc = load_json(ROOT / "registry/policies.json")
    topics_doc = load_json(ROOT / "routing/material3-topics.json")
    material_browser_evidence_path = ROOT / "routing/material3-browser-retrieval-evidence.json"
    integrated_material_pages: list[dict[str, Any]] = []
    if material_browser_evidence_path.is_file():
        # Fail closed on malformed/overstated page evidence. The scraper's
        # verified records remain distinct from the site's URL discovery data.
        if str(ROOT / "scripts") not in sys.path:
            sys.path.insert(0, str(ROOT / "scripts"))
        from material3_knowledge_pipeline import validate_evidence
        browser_evidence = load_json(material_browser_evidence_path)
        sitemap_doc = load_json(ROOT / "routing/material3-sitemap-evidence.json")
        validate_evidence(browser_evidence, topics_doc, sitemap_doc, root=ROOT)
        integrated_material_pages = [x for x in browser_evidence.get("records", []) if x.get("state") == "integrated"]
    source_by_id = {item["id"]: item for item in sources_doc["sources"]}
    skill_by_id = {item["id"]: item for item in skills_doc["skills"]}
    policy_by_id = {item["id"]: item for item in policies_doc["policies"]}
    topic_by_route = {item["taxonomy_id"]: item for item in topics_doc["topics"]}

    task_norm = normalized(task)
    task_compact = compact(task)
    route_matches: dict[str, dict[str, Any]] = {}
    evidence: list[dict[str, str]] = []
    negative_evidence: list[dict[str, str]] = []
    for route in taxonomy["selection_guidance"]:
        hits = []
        terms_by_normalized = {}
        for term in route.get("keywords", []) + route.get("signals", []):
            terms_by_normalized.setdefault(normalized(term), term)
        for term in sorted(terms_by_normalized.values(), key=lambda x: (normalized(x), x)):
            method = match_term(task_norm, task_compact, term)
            if method and term_is_negated(task_norm, term):
                negative_evidence.append({"domain": route["id"], "term": term, "match_method": method, "reason": "explicit_negation"})
            elif method:
                hits.append((term, method))
        if hits:
            route_matches[route["id"]] = route
            for term, method in hits:
                evidence.append({"domain": route["id"], "term": term, "match_method": method})

    # A harness-only route suppresses general/app implementation context unless the
    # task independently names an application domain; current route has explicit
    # exclusions so this behavior is visible and testable.
    suppressed: set[str] = set()
    for route in route_matches.values():
        suppressed.update(rid for rid in route.get("exclude_categories", []) if rid in route_matches)
    active_context_exclusions: list[tuple[str, dict[str, Any]]] = []
    for route_id, route in route_matches.items():
        for rule in route.get("context_exclusions", []):
            unless_any = rule.get("unless_any", [])
            if any(match_term(task_norm, task_compact, term) and not term_is_negated(task_norm, term) for term in unless_any):
                continue
            active_context_exclusions.append((route_id, rule))
            suppressed.update(rid for rid in rule.get("exclude_categories", []) if rid in route_matches)
    for rid in suppressed:
        route_matches.pop(rid, None)
    evidence = [row for row in evidence if row["domain"] in route_matches]

    broad_terms = sorted({term for route in route_matches.values() for term in route.get("ambiguity_if_only", [])}, key=normalized)
    stop = {"help", "please", "me", "with", "about", "implement", "improve", "review", "work", "on", "for"}
    significant = " ".join(word for word in task_norm.split() if word not in stop)
    ambiguity_reasons = []
    if not route_matches:
        for term in taxonomy.get("ambiguous_terms", []):
            if normalized(term) == significant:
                ambiguity_reasons.append(f"'{term}' is too broad to select a specific Android context")
        if not ambiguity_reasons:
            ambiguity_reasons.append("No configured domain keyword matched; Android-specific intent is unknown.")
        classification_status = "ambiguous" if len(ambiguity_reasons) and significant in {normalized(t) for t in taxonomy.get("ambiguous_terms", [])} else "unknown"
    else:
        if significant and any(normalized(term) == significant for term in broad_terms):
            ambiguity_reasons.append("The request names only a broad technology area; clarify the concrete change.")
        classification_status = "ambiguous" if ambiguity_reasons else ("multi_domain" if len(route_matches) > 1 else "matched")

    global_policy_ids = taxonomy["global_policy_ids"]
    selected_policy_ids = set(global_policy_ids)
    source_reasons: dict[str, set[str]] = {}
    knowledge_reasons: dict[str, set[str]] = {}
    skill_reasons: dict[str, set[str]] = {}
    material_route_ids: set[str] = set()
    required_verification: set[str] = set()
    category_exclusions: set[str] = set()
    negative_source_guards: set[str] = set()
    legacy_view_sources_selected: set[str] = set()

    for rid, route in route_matches.items():
        selected_policy_ids.update(route.get("policies", []))
        required_verification.update(route.get("freshness", []))
        required_verification.update(route.get("evidence", []))
        category_exclusions.update(route.get("exclude", []))
        negative_source_guards.update(route.get("exclude_source_ids", []))
        for source_id in route.get("source_ids", []):
            source_reasons.setdefault(source_id, set()).add(rid)
        for note in route.get("knowledge", []):
            knowledge_reasons.setdefault(note, set()).add(rid)
        for skill_id in route.get("skills", []):
            skill_reasons.setdefault(skill_id, set()).add(rid)
        if rid in topic_by_route:
            material_route_ids.add(rid)
            topic = topic_by_route[rid]
            for source_id in topic["source_registry_ids"] + topic["androidx_compose_apis"]["source_ids"]:
                source_reasons.setdefault(source_id, set()).add(rid)
            for note in topic["knowledge_references"]:
                knowledge_reasons.setdefault(note, set()).add(rid)
            for skill_id in topic["skill_ids"]:
                skill_reasons.setdefault(skill_id, set()).add(rid)
            selected_policy_ids.update(topic["policy_ids"])
            required_verification.update(topic["freshness_requirements"])
            legacy = topic.get("legacy_view_context", {})
            matched_view_term = next((term for term in legacy.get("activation_terms", []) if match_term(task_norm, task_compact, term) and not term_is_negated(task_norm, term)), None)
            if matched_view_term:
                reason = f"{rid}:explicit_view_xml_request"
                for source_id in legacy.get("source_ids", []):
                    source_reasons.setdefault(source_id, set()).add(reason)
                    legacy_view_sources_selected.add(source_id)
                for note in legacy.get("knowledge_references", []):
                    knowledge_reasons.setdefault(note, set()).add(reason)

    selected_material_pages: list[dict[str, Any]] = []
    for topic_id in sorted(material_route_ids):
        candidates = [x for x in integrated_material_pages if x.get("topic_id") == topic_id]
        if len(candidates) == 1:
            selected = candidates
        else:
            selected = [x for x in candidates if any(
                match_term(task_norm, task_compact, term) and not term_is_negated(task_norm, term)
                for term in x.get("routing_terms", [])
            )]
        for row in selected:
            relative = row["knowledge_reference"]
            knowledge_reasons.setdefault(relative, set()).add(f"{topic_id}:verified_material_page")
            source_reasons.setdefault("material3_site", set()).add(f"{topic_id}:verified_material_page")
            selected_material_pages.append(row)

    # Narrow route knowledge can be conditioned on task intent without changing
    # policy/source selection. Rules are local, declarative, and validated against
    # the source registry; they do not execute external text.
    for rid, route in route_matches.items():
        for rule in route.get("knowledge_rules", []):
            terms = rule.get("when_any", [])
            if not any(match_term(task_norm, task_compact, term) and not term_is_negated(task_norm, term) for term in terms):
                continue
            for note in rule.get("include", []):
                knowledge_reasons.setdefault(note, set()).add(rid)
            for note in rule.get("exclude", []):
                reasons_for_note = knowledge_reasons.get(note, set())
                reasons_for_note.discard(rid)
                if not reasons_for_note:
                    knowledge_reasons.pop(note, None)

    # Task-scoped exclusions remove only the named domains' contributions. If
    # another independently matched domain needs the same skill, policy, or note,
    # its selection reason is retained. Global mandatory policies are never removed.
    for route_id, rule in active_context_exclusions:
        excluded_reasons = set(rule.get("exclude_reasons", []))
        category_exclusions.add(f"{route_id}: context excluded because no explicit Material design intent matched")
        for collection, identifiers in (
            (source_reasons, rule.get("exclude_sources", [])),
            (knowledge_reasons, rule.get("exclude_knowledge", [])),
            (skill_reasons, rule.get("exclude_skills", [])),
        ):
            for identifier in identifiers:
                reasons = collection.get(identifier, set())
                reasons.difference_update(excluded_reasons)
                if not reasons:
                    collection.pop(identifier, None)
        for policy_id in rule.get("exclude_policies", []):
            selected_elsewhere = any(
                rid not in excluded_reasons and policy_id in route.get("policies", [])
                for rid, route in route_matches.items()
            ) or any(
                topic["taxonomy_id"] in material_route_ids and policy_id in topic["policy_ids"]
                for topic in topics_doc["topics"]
            )
            if policy_id not in global_policy_ids and not selected_elsewhere:
                selected_policy_ids.discard(policy_id)

    # Routes define a bounded eligible source set. Registry metadata enriches
    # provenance, authority, freshness, access, and task-relevance evidence; it
    # does not broaden selection to every source sharing a generic Compose tag.
    for source_id, reasons in source_reasons.items():
        source = source_by_id.get(source_id)
        if source:
            metadata_tags = set(source.get("relevant_tasks", []))
            source_domain = source.get("engineering_domain")
            reason_tags = {rid for rid in reasons if rid in metadata_tags or rid == source_domain}
            if reason_tags:
                reasons.update(reason_tags)

    for source_id in negative_source_guards:
        if source_id not in source_reasons:
            continue
        positive_routes = {
            rid for rid, route in route_matches.items()
            if source_id in route.get("source_ids", [])
        }
        guard_routes = {
            rid for rid, route in route_matches.items()
            if source_id in route.get("exclude_source_ids", [])
        }
        if positive_routes - guard_routes:
            continue
        source_reasons.pop(source_id)

    unknown_sources = sorted(set(source_reasons) - set(source_by_id))
    unknown_skills = sorted(set(skill_reasons) - set(skill_by_id))
    unknown_policies = sorted(selected_policy_ids - set(policy_by_id))
    if unknown_sources or unknown_skills or unknown_policies:
        raise ValueError(f"unresolved router references: sources={unknown_sources}, skills={unknown_skills}, policies={unknown_policies}")

    if project_config is not None:
        required_project_fields = {"schema_version", "harness_version", "androidx_dependencies", "gradle_versions", "architecture_constraints", "module_constraints"}
        missing_project_fields = required_project_fields - set(project_config)
        if missing_project_fields or project_config.get("schema_version") != 1:
            raise ValueError(f"incompatible target project context schema; expected schema_version=1 and fields {sorted(missing_project_fields)}")
        if not isinstance(project_config.get("androidx_dependencies"), dict) or not isinstance(project_config.get("gradle_versions"), dict) or not isinstance(project_config.get("architecture_constraints"), list) or not isinstance(project_config.get("module_constraints"), list):
            raise ValueError("invalid target project context field types")
        project_context = {"status": "provided_declarations_not_independently_verified", "project_id": project_config.get("project_id"), "androidx_dependencies": project_config["androidx_dependencies"], "gradle_versions": project_config["gradle_versions"], "architecture_constraints": project_config["architecture_constraints"], "module_constraints": project_config["module_constraints"], "source_files_observed": project_config.get("source_files_observed", []), "config_path": project_config_path}
    else:
        project_context = {"status": "not_provided", "project_id": None, "androidx_dependencies": {}, "gradle_versions": {}, "architecture_constraints": [], "module_constraints": [], "source_files_observed": [], "config_path": None}

    today = as_of or datetime.now(timezone.utc).date()
    windows = taxonomy["freshness_windows_days"]
    selected_sources = []
    missing_context = []
    freshness_records = []
    for source_id in sorted(source_reasons, key=lambda i: authority_rank(source_by_id[i])):
        source = source_by_id[source_id]
        source_status = source["accessibility_status"]
        verified = date.fromisoformat(source["last_verified"])
        age = (today - verified).days
        window = windows.get(source.get("version_sensitivity", "high"), windows["high"])
        if age < 0:
            age_status = "invalid_future_registry_date"
        elif age > window:
            age_status = "stale_by_registry_date"
        else:
            age_status = "within_review_window_not_live_verified"
        live_required = source.get("version_sensitivity") == "high" or source_status not in ("retrieved", "retrieved_selected")
        freshness_records.append({"source_id": source_id, "last_verified": source["last_verified"], "age_days": age, "review_window_days": window, "registry_age_status": age_status, "live_verification_required": live_required, "live_verification_performed": False})
        selected_sources.append({"id": source_id, "title": source["title"], "canonical_url": source["canonical_url"], "owner": source["owner"], "source_type": source["source_type"], "authority_level": source["authority_level"], "engineering_domain": source["engineering_domain"], "relevant_tasks": source["relevant_tasks"], "version_sensitivity": source["version_sensitivity"], "retrieval_method": source["retrieval_method"], "accessibility_status": source_status, "local_knowledge_reference": source["local_knowledge_reference"], "known_limitations": source["known_limitations"], "last_verified": source["last_verified"], "selected_because_of": sorted(source_reasons[source_id])})
        if source_status not in ("retrieved", "retrieved_selected"):
            detail = source["known_limitations"]
            if source_id == "figma_m3_kit" and "token" in task_norm:
                detail += " No exact token values, numeric tokens, or Figma layers were extracted."
            missing_context.append({"kind": "source_access_limitation", "source_id": source_id, "status": source_status, "detail": detail, "required_action": "Re-fetch/inspect the canonical source or use an explicitly authorized export; do not infer its contents."})
        if live_required:
            missing_context.append({"kind": "live_verification_not_performed", "source_id": source_id, "status": "not_performed_by_router", "detail": "Registry freshness is metadata only; no external request or target-project compatibility check was made.", "required_action": "Recheck this source and exact target dependency before implementation."})

    selected_urls_by_topic: dict[str, set[str]] = {}
    for row in selected_material_pages:
        selected_urls_by_topic.setdefault(row["topic_id"], set()).add(row["canonical_url"])
    for topic_id in sorted(material_route_ids):
        topic = topic_by_route[topic_id]
        page_records = [x for x in integrated_material_pages if x.get("topic_id") == topic_id]
        verified_urls = {x["canonical_url"] for x in page_records}
        remaining = sorted(set(topic["canonical_source_urls"]) - verified_urls)
        missing_context.append({"kind": "material_page_content_unverified", "topic_id": topic_id, "status": "partially_verified" if verified_urls else topic["source_access_status"], "verified_page_urls": sorted(verified_urls), "selected_verified_page_urls": sorted(selected_urls_by_topic.get(topic_id, set())), "unverified_url_count": len(remaining), "discovered_url_registry": "routing/material3-topics.json", "detail": "Only the listed page bodies have reviewed, integrated knowledge; other discovered pages remain unverified. " + topic["retrieval_limitations"], "required_action": "Retrieve and inspect the exact Material.io page before making page-specific claims not covered by an integrated note."})

    selected_knowledge = []
    estimate = 0
    for relative in sorted(knowledge_reasons):
        path = safe_path(relative)
        if not path.is_file():
            raise ValueError(f"selected knowledge reference is missing: {relative}")
        chars = len(path.read_text(encoding="utf-8"))
        estimate += chars
        source_ids_for_note = sorted(s["id"] for s in source_by_id.values() if s["local_knowledge_reference"] == relative)
        if not source_ids_for_note and any(x.get("knowledge_reference") == relative for x in selected_material_pages):
            source_ids_for_note = ["material3_site"]
        selected_knowledge.append({"path": relative, "character_count": chars, "source_ids": source_ids_for_note, "selected_because_of": sorted(knowledge_reasons[relative]), "mandatory_for_this_route": True, "content_read_by_router": False})

    selected_skills = []
    for skill_id in sorted(skill_reasons):
        skill = skill_by_id[skill_id]
        path = safe_path(skill["path"])
        if not path.is_file():
            raise ValueError(f"selected skill file is missing: {skill['path']}")
        chars = len(path.read_text(encoding="utf-8"))
        selected_skills.append({"id": skill_id, "path": skill["path"], "origin": skill["origin"], "selected_because_of": sorted(skill_reasons[skill_id]), "activation": "recommended_not_activated", "discovery": "Codex-native SKILL.md convention; this router only recommends it", "character_count": chars})
    estimate += sum(len(policy_by_id[pid]["summary"]) for pid in selected_policy_ids)
    budget = budget_chars if budget_chars is not None else taxonomy["default_context_budget_chars"]
    if budget <= 0:
        raise ValueError("context budget must be a positive character count")
    budget_status = "within_budget" if estimate <= budget else "mandatory_context_exceeds_limit"

    selected_policies = []
    for pid in sorted(selected_policy_ids):
        reasons = {"global_mandatory"} if pid in global_policy_ids else set()
        reasons.update(rid for rid, route in route_matches.items() if pid in route.get("policies", []))
        reasons.update(t["taxonomy_id"] for t in topics_doc["topics"] if t["taxonomy_id"] in material_route_ids and pid in t["policy_ids"])
        selected_policies.append({"id": pid, "summary": policy_by_id[pid]["summary"], "mandatory": pid in global_policy_ids, "selected_because_of": sorted(reasons)})

    required_verification.update([
        "No external source was fetched by this router; perform any listed live check before relying on current APIs or page-specific guidance.",
        "Run relevant project checks and report their actual results; the router does not execute Android builds or tests.",
    ])
    if material_route_ids and not legacy_view_sources_selected:
        category_exclusions.add("Google Material Components Android references use the legacy View/XML toolkit; excluded unless the task explicitly requests View/XML or MDC-Android context.")
    if legacy_view_sources_selected:
        required_verification.add("Selected Material Components Android documentation describes View/XML APIs at a pinned library revision; do not port its classes, attributes, or behavior into Compose. Verify any existing legacy project's exact dependency and prefer AndroidX references for Compose.")
    if route_matches:
        if not project_context["androidx_dependencies"]:
            required_verification.add("Target project AndroidX dependency declarations are absent; inspect version catalogs/build files and resolved dependencies before making API or experimental-API compatibility claims.")
        else:
            required_verification.add("Target project context records declarations only; confirm resolved AndroidX artifacts and versions from the target project's build before API compatibility claims.")
        if project_context["architecture_constraints"] or project_context["module_constraints"]:
            required_verification.add("Compare selected general guidance with declared project architecture/module constraints; surface conflicts and require an explicit project-owner decision before changing those constraints.")
    if classification_status in {"unknown", "ambiguous"}:
        required_verification.add("Clarify the requested change before implementation; do not infer Android-specific intent from an unknown or broad task.")
    if any(x["live_verification_required"] for x in freshness_records):
        required_verification.add("Recheck selected version-sensitive/limited sources live; registry dates are provenance, not proof of current compatibility.")

    if classification_status == "unknown":
        routing_status = "uncertain_no_domain_match"
    elif classification_status == "ambiguous":
        routing_status = "ambiguous_clarification_recommended"
    elif missing_context or budget_status != "within_budget":
        routing_status = "routed_with_limitations"
    else:
        routing_status = "routed"

    return {
        "schema_version": 2,
        "router_version": ROUTER_VERSION,
        "input_task": task,
        "normalized_task": task_norm,
        "as_of_date": today.isoformat(),
        "classification": {"status": classification_status, "matched_domains": sorted(route_matches), "match_evidence": sorted(evidence, key=lambda x: (x["domain"], normalized(x["term"]), x["match_method"])), "negative_match_evidence": sorted(negative_evidence, key=lambda x: (x["domain"], normalized(x["term"]))), "ambiguity_reasons": ambiguity_reasons},
        "selected_sources": selected_sources,
        "selected_knowledge_references": selected_knowledge,
        "selected_skills": selected_skills,
        "skill_execution_evidence": {
            "repository_skill_files_present": True,
            "codex_native_discovery": "not_observed_by_router",
            "recommended_skill_ids": sorted(skill_reasons),
            "skill_invocation": "not_observed",
            "skill_md_read_by_session": "not_observed",
            "selected_knowledge_read_by_session": "not_observed",
            "external_freshness_verified": False,
            "evidence_contract": "Record only observable session/tool evidence; routing, path existence, or task relevance do not prove native activation, file reading, or live source verification."
        },
        "selected_policies": selected_policies,
        "required_verification_actions": sorted(required_verification),
        "freshness": {"live_checks_performed": False, "source_records": freshness_records},
        "missing_or_inaccessible_context": sorted(missing_context, key=lambda x: (x["kind"], x.get("source_id", x.get("topic_id", "")))),
        "context_budget": {"unit": "characters", "limit_chars": budget, "estimated_selected_chars": estimate, "status": budget_status, "strategy": "Budget estimates selected local knowledge notes and policy summaries. Skill bodies are separately reported because Codex activation is not controlled by this router. No arbitrary truncation; if knowledge exceeds the limit, raise the budget or explicitly defer whole references and record that choice.", "potential_native_skill_instruction_chars": sum(x["character_count"] for x in selected_skills)},
        "material3_topics": [{"id": t["id"], "title": t["title"], "canonical_source_url": t["canonical_source_url"], "additional_urls_available_in_manifest": t["canonical_source_url_count"] - 1, "manifest_path": "routing/material3-topics.json", "source_access_status": t["source_access_status"], "selected_verified_page_urls": sorted(selected_urls_by_topic.get(t["taxonomy_id"], set())), "retrieval_limitations": t["retrieval_limitations"]} for t in sorted(topics_doc["topics"], key=lambda x: x["id"]) if t["taxonomy_id"] in material_route_ids],
        "material3_page_evidence": [{"topic_id": x["topic_id"], "canonical_url": x["canonical_url"], "title": x.get("document_title"), "state": x["state"], "content_fingerprint": x["content_fingerprint"], "knowledge_reference": x["knowledge_reference"], "reviewed_at": x["reviewed_at"], "freshness_requirements": x["freshness_requirements"], "review_age_days": (today - date.fromisoformat(x["reviewed_at"])).days, "review_freshness_status": "stale_by_review_date" if (today - date.fromisoformat(x["reviewed_at"])).days > windows.get(source_by_id["material3_site"].get("version_sensitivity", "high"), windows["high"]) else "within_review_window", "live_verification_required": (today - date.fromisoformat(x["reviewed_at"])).days > windows.get(source_by_id["material3_site"].get("version_sensitivity", "high"), windows["high"]), "selected_for_task": x in selected_material_pages} for x in sorted((p for p in integrated_material_pages if p["topic_id"] in material_route_ids), key=lambda x: (x["topic_id"], x["canonical_url"]))],
        "target_project_context": project_context,
        "explicit_exclusions": {"category_rules": sorted(category_exclusions), "excluded_categories": sorted(suppressed), "negative_source_guards": sorted(negative_source_guards - set(source_reasons)), "negated_terms": [{"domain": x["domain"], "term": x["term"], "reason": x["reason"]} for x in sorted(negative_evidence, key=lambda x: (x["domain"], normalized(x["term"]))) ]},
        "routing_status": routing_status,
        "router_does_not": ["activate Codex skills", "fetch external URLs", "assert selected documents were read", "execute Android builds/tests", "invent unavailable design tokens or API signatures"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Natural-language engineering task")
    parser.add_argument("--budget-chars", type=int, help="Override context character budget")
    parser.add_argument("--as-of", type=date.fromisoformat, help="Freeze freshness evaluation date (YYYY-MM-DD)")
    parser.add_argument("--project-config", type=Path, help="Optional target repository project-context JSON; declarations are not treated as resolved versions")
    args = parser.parse_args()
    try:
        config = None
        if args.project_config:
            config = load_json(args.project_config)
        print(json.dumps(build_manifest(args.task, as_of=args.as_of, budget_chars=args.budget_chars, project_config=config, project_config_path=str(args.project_config) if args.project_config else None), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"route_context: ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
