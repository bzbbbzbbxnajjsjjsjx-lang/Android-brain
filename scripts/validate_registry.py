#!/usr/bin/env python3
"""Validate source, skill, policy, routing, and Material topic metadata."""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("ANDROID_HARNESS_ROOT", Path(__file__).resolve().parents[1])).resolve()
IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")


def load(relative: str) -> dict:
    try:
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {relative}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def unique(items: list, label: str) -> dict:
    result = {}
    require(isinstance(items, list), f"{label} must be a list")
    for item in items:
        key = item.get("id")
        require(isinstance(key, str) and key, f"{label} entry missing id")
        pattern = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$") if label == "skill" else IDENTIFIER
        require(pattern.fullmatch(key), f"{label} id has invalid stable syntax: {key}")
        require(key not in result, f"duplicate {label} id: {key}")
        result[key] = item
    return result


def local_file(relative: str, message: str) -> Path:
    path = (ROOT / relative).resolve()
    require(path.is_relative_to(ROOT), f"path escapes repository: {relative}")
    require(path.is_file(), message)
    return path


def main() -> int:
    try:
        source_doc = load("registry/sources.json")
        skill_doc = load("registry/skills.json")
        policy_doc = load("registry/policies.json")
        taxonomy = load("routing/task-taxonomy.json")
        topics_doc = load("routing/material3-topics.json")
        manifest_schema = load("routing/context-manifest.schema.json")
        evidence_schema = load("policies/evidence.schema.json")
        gate_schema = load("policies/quality-gate-result.schema.json")
        sitemap = load("routing/material3-sitemap-evidence.json")
        require(source_doc.get("schema_version") == 1, "unsupported source registry schema")
        for schema_name, schema in (("evidence", evidence_schema), ("quality gate result", gate_schema)):
            require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{schema_name}: unsupported schema draft")
            require(schema.get("type") == "object" and schema.get("required"), f"{schema_name}: schema is incomplete")
        try:
            from jsonschema import Draft202012Validator
            Draft202012Validator.check_schema(evidence_schema)
            Draft202012Validator.check_schema(gate_schema)
        except ImportError as exc:
            raise ValueError("jsonschema is required for schema checks; install requirements-dev.txt") from exc
        except Exception as exc:
            raise ValueError(f"invalid policy/evidence JSON Schema: {exc}") from exc
        require(skill_doc.get("schema_version") == 1, "unsupported skill registry schema")
        require(policy_doc.get("schema_version") == 1, "unsupported policy registry schema")
        require(taxonomy.get("schema_version") == 2, "unsupported task taxonomy schema")
        require(taxonomy.get("status") == "deterministic_keyword_router_v1", "task taxonomy is not marked for deterministic routing")
        require(topics_doc.get("schema_version") == 1, "unsupported Material topic manifest schema")
        require(manifest_schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "unsupported context manifest schema draft")
        require({"schema_version", "classification", "selected_sources", "selected_knowledge_references", "selected_skills", "selected_policies", "context_budget", "routing_status", "router_does_not"}.issubset(manifest_schema.get("required", [])), "context manifest output schema is incomplete")

        source_fields = {
            "id", "title", "canonical_url", "owner", "source_type", "authority_level",
            "engineering_domain", "relevant_tasks", "retrieval_method", "related_skills",
            "related_policies", "version_sensitivity", "last_verified", "accessibility_status",
            "local_knowledge_reference", "known_limitations",
        }
        sources = unique(source_doc.get("sources", []), "source")
        skills = unique(skill_doc.get("skills", []), "skill")
        policies = unique(policy_doc.get("policies", []), "policy")
        if "enforcement_schema_version" in policy_doc:
            modes = {"deterministic_automated", "runtime_tool_dependent", "manual_review", "advisory_guidance"}
            rules = {"source_provenance", "source_access_claims", "api_compatibility", "experimental_api", "manual_design_review", "manual_architecture_review", "dependency_selection", "scope_isolation", "visual_baseline_approval", "measurement_first", "performance_claims", "reporting_integrity", "api_verification", "security_artifacts", "source_freshness", "api_claim_provenance", "testing_execution", "manual_accessibility_review"}
            require(policy_doc["enforcement_schema_version"] == 1, "unsupported policy enforcement schema")
            require(set(policy_doc.get("supported_enforcement_modes", [])) == modes, "policy enforcement modes are incomplete")
            fields = {"id", "summary", "category", "description", "applicability", "enforcement_mode", "required_evidence", "evaluation", "failure_severity", "remediation_guidance", "exception_handling", "source_provenance"}
            for policy in policies.values():
                require(fields <= set(policy), f"{policy['id']}: incomplete enforceable policy definition")
                require(policy["enforcement_mode"] in modes, f"{policy['id']}: unknown enforcement mode")
                require(policy["evaluation"].get("rule_id") in rules, f"{policy['id']}: rule is not in evaluator allowlist")
                require(policy["required_evidence"] and all(isinstance(x, str) and x for x in policy["required_evidence"]), f"{policy['id']}: required_evidence cannot be empty")
                require(policy["applicability"].get("basis") in {"global_mandatory", "router_selected", "claim_triggered"}, f"{policy['id']}: invalid applicability basis")
                require(all(isinstance(policy["applicability"].get(key), list) for key in ("claim_types", "task_kinds")), f"{policy['id']}: applicability conditions must be explicit lists")
                require(policy["failure_severity"] in {"critical", "high", "medium", "low", "advisory"}, f"{policy['id']}: invalid severity")
                require(isinstance(policy["exception_handling"].get("allowed"), bool) and policy["exception_handling"].get("requirement"), f"{policy['id']}: exception handling must be explicit")
                require(set(policy["source_provenance"]) == {"source_ids", "repository_references", "knowledge_references"}, f"{policy['id']}: source provenance fields differ from schema")
                for sid in policy["source_provenance"].get("source_ids", []):
                    require(sid in sources, f"{policy['id']}: unknown provenance source {sid}")
                for ref in policy["source_provenance"].get("repository_references", []) + policy["source_provenance"].get("knowledge_references", []):
                    local_file(ref, f"{policy['id']}: missing policy reference {ref}")
        require(len(sources) >= 17, "registry must include every supplied source")
        urls = [s.get("canonical_url") for s in sources.values()]
        require(len(urls) == len(set(urls)), "duplicate canonical URL")

        for source in sources.values():
            require(source_fields == set(source), f"{source['id']}: source fields differ from schema")
            require(source["canonical_url"].startswith("https://"), f"{source['id']}: URL must be HTTPS")
            require(re.fullmatch(r"\d{4}-\d\d-\d\d", source["last_verified"]), f"{source['id']}: invalid verification date")
            note = source["local_knowledge_reference"]
            content = local_file(note, f"{source['id']}: missing knowledge note {note}").read_text(encoding="utf-8")
            require(source["id"] in content, f"{source['id']}: provenance absent from {note}")
            for ident in source["related_skills"]:
                require(ident in skills, f"{source['id']}: unknown skill {ident}")
            for ident in source["related_policies"]:
                require(ident in policies, f"{source['id']}: unknown policy {ident}")

        for skill in skills.values():
            path = local_file(skill["path"], f"{skill['id']}: missing {skill['path']}")
            content = path.read_text(encoding="utf-8")
            require(content.startswith("---\n"), f"{skill['id']}: missing SKILL.md frontmatter")
            header = content.split("---\n", 2)[1]
            require(re.search(rf"(?m)^name:\s*{re.escape(skill['id'])}\s*$", header), f"{skill['id']}: frontmatter name mismatch")
            require(re.search(r"(?m)^description:\s*\S", header), f"{skill['id']}: missing description")

        routes = unique(taxonomy.get("selection_guidance", []), "routing category")
        require(len(routes) >= 21, "task taxonomy must include broad Material 3 topic routes")
        for pid in taxonomy.get("global_policy_ids", []):
            require(pid in policies, f"unknown mandatory global policy: {pid}")
        required_global = {"security", "provenance", "scope_isolation", "source_access", "reporting", "testing_evidence"}
        require(required_global.issubset(taxonomy.get("global_policy_ids", [])), "global mandatory safety/provenance/evidence policies are incomplete")
        for pid in taxonomy["global_policy_ids"]:
            require(policies[pid]["exception_handling"]["allowed"] is False, f"global mandatory policy cannot be waived: {pid}")
            require(policies[pid]["applicability"].get("basis") == "global_mandatory", f"global policy applicability was weakened: {pid}")
            require(policies[pid]["enforcement_mode"] != "advisory_guidance", f"global mandatory policy cannot be advisory: {pid}")
            require(policies[pid]["failure_severity"] in {"critical", "high"}, f"global mandatory policy severity was weakened: {pid}")
        for route in routes.values():
            for key in ("keywords", "source_ids", "knowledge", "skills", "policies", "freshness", "evidence", "exclude"):
                require(isinstance(route.get(key), list), f"{route['id']}: missing/list-invalid {key}")
            require(route["keywords"], f"{route['id']}: no deterministic match terms")
            for sid in route["source_ids"]:
                require(sid in sources, f"{route['id']}: unknown source {sid}")
            for path in route["knowledge"]:
                local_file(path, f"{route['id']}: missing knowledge note {path}")
            for rule in route.get("knowledge_rules", []):
                require(isinstance(rule, dict) and isinstance(rule.get("when_any"), list) and rule["when_any"], f"{route['id']}: knowledge rule requires match terms")
                require(isinstance(rule.get("include", []), list) and isinstance(rule.get("exclude", []), list), f"{route['id']}: invalid knowledge rule paths")
                for path in rule.get("include", []) + rule.get("exclude", []):
                    local_file(path, f"{route['id']}: missing conditional knowledge note {path}")
            for ident in route["skills"]:
                require(ident in skills, f"{route['id']}: unknown skill {ident}")
            for ident in route["policies"]:
                require(ident in policies, f"{route['id']}: unknown policy {ident}")
            for sid in route.get("exclude_source_ids", []):
                require(sid in sources, f"{route['id']}: unknown excluded source {sid}")
            for rid in route.get("exclude_categories", []):
                require(rid in routes, f"{route['id']}: unknown excluded route {rid}")

        topics = unique(topics_doc.get("topics", []), "Material topic")
        sitemap_path = topics_doc.get("sitemap_evidence_path")
        require(sitemap_path == "routing/material3-sitemap-evidence.json", "Material sitemap provenance path mismatch")
        require(sitemap["provenance"]["sitemap_url"] == "https://m3.material.io/sitemap.xml", "unexpected Material sitemap source")
        require(sitemap["provenance"]["http_status"] == 200, "Material sitemap was not successfully retrieved")
        sitemap_urls = set(sitemap.get("urls", []))
        require(len(sitemap_urls) >= 200, "Material sitemap evidence is incomplete")
        require(len(sitemap_urls) == sitemap["provenance"]["included_active_design_url_count"], "Material sitemap evidence URL count mismatch")
        require(len(sitemap_urls) == len(sitemap["urls"]), "duplicate URL in Material sitemap evidence")
        require(all(u.startswith("https://m3.material.io/foundations/") or u.startswith("https://m3.material.io/styles/") or u.startswith("https://m3.material.io/components/") for u in sitemap_urls), "sitemap evidence contains out-of-scope paths")
        for topic in topics.values():
            for field in ("taxonomy_id", "canonical_source_url", "canonical_source_urls", "classification", "source_registry_ids", "related_tasks", "androidx_compose_apis", "knowledge_references", "source_access_status", "design_spec_accessibility_status", "retrieval_limitations", "freshness_requirements", "policy_ids", "skill_ids"):
                require(field in topic, f"{topic['id']}: missing Material topic field {field}")
            require(topic["taxonomy_id"] in routes, f"{topic['id']}: no matching route")
            require(topic["classification"] == "material_io_design_specification", f"{topic['id']}: Material.io must remain distinct from implementation APIs")
            require(topic["canonical_source_urls"], f"{topic['id']}: no canonical Material URLs")
            for url in topic["canonical_source_urls"]:
                require(url.startswith("https://m3.material.io/"), f"{topic['id']}: noncanonical Material URL {url}")
                require(url in sitemap_urls, f"{topic['id']}: URL was not found in retrieved sitemap: {url}")
            require(topic["canonical_source_url"] in topic["canonical_source_urls"], f"{topic['id']}: primary URL absent from its URL set")
            require(topic["canonical_source_url_count"] == len(topic["canonical_source_urls"]), f"{topic['id']}: URL count metadata mismatch")
            for sid in topic["source_registry_ids"]:
                require(sid in sources, f"{topic['id']}: unknown Material source {sid}")
            for sid in topic["androidx_compose_apis"]["source_ids"]:
                require(sid in sources and sources[sid]["source_type"] in ("api_reference", "implementation_guide"), f"{topic['id']}: API source is missing or misclassified: {sid}")
            for path in topic["knowledge_references"]:
                local_file(path, f"{topic['id']}: missing knowledge reference {path}")
            for ident in topic["policy_ids"]:
                require(ident in policies, f"{topic['id']}: unknown policy {ident}")
            for ident in topic["skill_ids"]:
                require(ident in skills, f"{topic['id']}: unknown skill {ident}")
            require(topic["source_access_status"] in {"sitemap_listed_content_not_individually_retrieved", "partial_js_shell_confirmed"}, f"{topic['id']}: content accessibility is overstated")

        required_topics = {"material3_foundations", "material3_expressive", "material3_color", "material3_typography", "material_shapes", "material_motion", "material3_layout", "material3_adaptive", "material3_components", "material3_component_states", "material3_interaction", "material3_accessibility", "material3_tokens", "material3_navigation", "material3_spacing_density", "material3_elevation", "material3_icons", "material3_content_design", "material3_watches", "material3_xr", "material3_co_design"}
        require(required_topics.issubset(topics), f"Material 3 coverage missing {sorted(required_topics - set(topics))}")
        material_skill = skills.get("material3-expressive")
        require(material_skill is not None, "unified Material 3 skill is missing")
        material_topic_ids = {topic["taxonomy_id"] for topic in topics.values()}
        require(material_topic_ids.issubset(set(material_skill.get("domains", []))), "unified Material 3 skill metadata does not cover every topic")
        for topic in topics.values():
            require("material3-expressive" in topic["skill_ids"], f"{topic['id']}: missing unified Material 3 skill")
        require(len(topics["material3_components"]["canonical_source_urls"]) >= 100, "Material component catalog coverage unexpectedly small")
        require(len(topics["material3_accessibility"]["canonical_source_urls"]) >= 30, "Material accessibility path coverage unexpectedly small")
        covered_urls = set().union(*(set(topic["canonical_source_urls"]) for topic in topics.values()))
        require(covered_urls == sitemap_urls, f"Material topic coverage mismatch: {len(sitemap_urls - covered_urls)} sitemap pages uncovered, {len(covered_urls - sitemap_urls)} unknown URLs")

        print(f"PASS: {len(sources)} sources, {len(skills)} skills, {len(policies)} policies, {len(routes)} routing categories; registry references resolve.")
        print(f"PASS: {len(topics)} Material 3 topics cover all {len(sitemap_urls)} active foundations/styles/components sitemap URLs; every URL is backed by the retrieved official sitemap.")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
