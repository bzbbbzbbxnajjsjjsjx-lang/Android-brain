#!/usr/bin/env python3
"""Contrasting routing/size checks for context-efficient Android task selection."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("route_context_efficiency", ROOT / "scripts/route_context.py")
router = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = router
spec.loader.exec_module(router)
AS_OF = date(2026, 10, 15)
GLOBAL = {"security", "provenance", "scope_isolation", "source_access", "reporting", "testing_evidence", "freshness", "no_hallucinated_api"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def route(task: str) -> dict:
    manifest = router.build_manifest(task, as_of=AS_OF)
    schema = json.loads((ROOT / "routing/context-manifest.schema.json").read_text(encoding="utf-8"))
    require(set(schema["required"]) <= set(manifest), "context manifest is missing required fields")
    mandatory = {item["id"] for item in manifest["selected_policies"] if item["mandatory"]}
    require(GLOBAL <= mandatory, "context minimization removed a mandatory global policy")
    for key, field in (("selected_sources", "id"), ("selected_skills", "id"), ("selected_policies", "id"), ("selected_knowledge_references", "path")):
        values = [item[field] for item in manifest[key]]
        require(len(values) == len(set(values)), f"duplicate selected {key}")
    return manifest


def ids(manifest: dict, key: str) -> set[str]:
    return {item["id"] for item in manifest[key]}


def knowledge(manifest: dict) -> set[str]:
    return {item["path"] for item in manifest["selected_knowledge_references"]}


def sources(manifest: dict) -> set[str]:
    return ids(manifest, "selected_sources")


def skills(manifest: dict) -> set[str]:
    return ids(manifest, "selected_skills")


def topics(manifest: dict) -> set[str]:
    return {item["id"] for item in manifest["material3_topics"]}


def metrics(label: str, manifest: dict) -> None:
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
    selected_knowledge_chars = sum(item["character_count"] for item in manifest["selected_knowledge_references"])
    policy_chars = sum(len(item["summary"]) for item in manifest["selected_policies"])
    skill_chars = sum(item["character_count"] for item in manifest["selected_skills"])
    print(
        f"MEASURE {label}: manifest_json_chars={len(serialized)}, "
        f"skills={len(manifest['selected_skills'])}, knowledge_files={len(manifest['selected_knowledge_references'])}, "
        f"selected_policies={len(manifest['selected_policies'])}, "
        f"knowledge_chars={selected_knowledge_chars}, policy_summary_chars={policy_chars}, "
        f"skill_file_chars_if_read={skill_chars}."
    )


def run() -> None:
    narrow = route("Add a narrow Compose accessibility test for screen reader semantics.")
    narrow_domains = set(narrow["classification"]["matched_domains"])
    require({"compose_ui", "compose_accessibility_testing"} <= narrow_domains, "narrow accessibility test missed Compose/testing routes")
    require("material3_accessibility" not in narrow_domains and not topics(narrow), "test-only accessibility task retained Material 3 domain context")
    require(skills(narrow) == {"kotlin-compose", "android-testing"}, f"test-only skills are not selective: {skills(narrow)}")
    require(knowledge(narrow) == {"knowledge/androidx/compose-accessibility.md"}, f"test-only knowledge is not selective: {knowledge(narrow)}")
    require(not ({"material3_site", "androidx_material3_package"} & sources(narrow)), "test-only task selected Material-specific sources")
    require({"accessibility_review", "api_compatibility"} <= ids(narrow, "selected_policies"), "test-only task lost accessibility or API compatibility requirements")
    require("design_compliance" not in ids(narrow, "selected_policies"), "test-only task retained a visual design review policy")
    missing_material = [item for item in narrow["missing_or_inaccessible_context"] if item["kind"] == "material_page_content_unverified"]
    require(not missing_material, "test-only task surfaced irrelevant unverified Material.io content")
    metrics("compose_accessibility_test_only", narrow)

    expressive = route("Implement Material 3 Expressive navigation components in Jetpack Compose with accessibility.")
    expressive_domains = set(expressive["classification"]["matched_domains"])
    require({"material3_expressive", "material3_navigation", "material3_components", "material3_accessibility"} <= expressive_domains, "Material 3 Expressive implementation lost design domains")
    require("material3-expressive" in skills(expressive), "Material 3 skill was incorrectly removed from Material implementation")
    require("material3_site" in sources(expressive), "Material design source/provenance was omitted")
    require(any(item["accessibility_status"] == "partial_js_shell" for item in expressive["selected_sources"] if item["id"] == "material3_site"), "Material.io access limitation was hidden")
    require("knowledge/androidx/compose-accessibility.md" in knowledge(expressive), "Compose accessibility implementation note missing")
    metrics("material3_expressive_ui", expressive)

    performance = route("Optimize Jetpack Compose scrolling performance with Macrobenchmark.")
    require("performance" in performance["classification"]["matched_domains"], "Compose performance route did not match")
    require("android-performance" in skills(performance) and "kotlin-compose" in skills(performance), "performance/Compose expertise missing")
    require(not ({"material3-expressive", "visual-design-validation"} & skills(performance)), "performance task selected unrelated design skills")
    require(not ({"material3_site", "material3_motion", "material_shape_principles"} & sources(performance)), "performance task selected Material design sources")
    metrics("compose_performance", performance)

    visual = route("Perform a visual design review and assess hierarchy of an existing Compose screen.")
    require("visual_design_review" in visual["classification"]["matched_domains"], "visual design review route did not match")
    require("visual-design-validation" in skills(visual), "visual review expertise missing")
    require("material3-expressive" not in skills(visual), "generic visual review loaded Material 3 skill")
    require("material3_site" not in sources(visual) and "knowledge/material3/principles.md" not in knowledge(visual), "generic visual review loaded unrequested Material context")
    require("design_compliance" in ids(visual, "selected_policies"), "visual review lost the manual design compliance contract")
    metrics("visual_design_review", visual)

    combined = route("Implement Material 3 Expressive components in Compose with accessibility, and add a Compose accessibility test.")
    combined_domains = set(combined["classification"]["matched_domains"])
    require({"compose_accessibility_testing", "material3_accessibility", "material3_expressive", "material3_components"} <= combined_domains, "combined Material/accessibility task lost a domain")
    require({"material3-expressive", "android-testing", "visual-design-validation"} <= skills(combined), "combined task lost relevant design/testing skills")
    require("material3_site" in sources(combined), "combined task lost Material provenance")
    require({"accessibility_review", "design_compliance", "api_compatibility"} <= ids(combined, "selected_policies"), "combined task lost applicable policies")
    metrics("combined_accessibility_material3", combined)

    # Repeatability: same input, date, registry and router produce identical logical JSON.
    replay = route("Add a narrow Compose accessibility test for screen reader semantics.")
    require(json.dumps(narrow, sort_keys=True) == json.dumps(replay, sort_keys=True), "same route inputs produced different manifests")
    print("PASS: five contrasting task classes select relevant knowledge/skills and exclude irrelevant Material, visual, or performance context.")
    print("PASS: mandatory global policies, applicable accessibility/API/design policies, source freshness, and access status remain intact.")
    print("PASS: identical task and registry state produce deterministic output.")
    print("NOT VERIFIED: token count and native skill invocation; router reports selected paths/recommendations only.")


if __name__ == "__main__":
    try:
        run()
    except (AssertionError, KeyError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
