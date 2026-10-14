#!/usr/bin/env python3
"""Positive and negative evaluations for deterministic Android context routing."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("route_context", ROOT / "scripts/route_context.py")
router = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = router
spec.loader.exec_module(router)
AS_OF = date(2026, 10, 14)


def route(task: str, budget: int | None = None) -> dict:
    return router.build_manifest(task, as_of=AS_OF, budget_chars=budget)


def ids(manifest: dict, key: str) -> set[str]:
    return {item["id"] for item in manifest[key]}


def source_ids(manifest: dict) -> set[str]:
    return ids(manifest, "selected_sources")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run() -> None:
    cases = []

    # A: M3 motion + Compose; no unrelated architecture or startup context.
    a = route("Implement Material 3 Expressive motion in Jetpack Compose.")
    require({"material_motion", "androidx_motion_scheme", "material3_site"} <= source_ids(a), "A missing Material/AndroidX motion source")
    require("material3-expressive" in ids(a, "selected_skills"), "A missing comprehensive Material 3 motion skill")
    require({"design_compliance", "accessibility_review", "visual_baseline_approval"} <= ids(a, "selected_policies"), "A missing design/validation policy")
    require(not ({"hilt_android", "baseline_profiles", "macrobenchmark"} & source_ids(a)), "A loaded unrelated Hilt/performance source")
    cases.append(("A Material 3 Expressive Motion", a))

    # B: API, shape principles, experimental and dependency checks.
    b = route("Implement animated MaterialShapes in Compose.")
    require({"material_shape_principles", "material_shapes_api"} <= source_ids(b), "B missing shape design/API source")
    require({"experimental_api", "api_compatibility", "no_hallucinated_api", "accessibility_review"} <= ids(b, "selected_policies"), "B missing experimental/dependency/accessibility verification")
    cases.append(("B MaterialShapes", b))

    # C: proves the router spans Material beyond motion/shape.
    c = route("Design a complete Material 3 Expressive design system including typography, color, layout, adaptive components, navigation, accessibility, shapes, and motion.")
    topics = {item["id"] for item in c["material3_topics"]}
    required = {"material3_foundations", "material3_expressive", "material3_color", "material3_typography", "material3_layout", "material3_adaptive", "material3_components", "material3_navigation", "material3_accessibility", "material3_tokens", "material3_spacing_density", "material3_component_states", "material3_interaction", "material_shapes", "material_motion"}
    require(required <= topics, f"C Material domain is incomplete: {sorted(required - topics)}")
    require({"androidx_color_scheme", "androidx_typography", "androidx_material_theme", "androidx_motion_scheme", "material_shapes_api"} <= source_ids(c), "C missing AndroidX implementation verification")
    require({"design_compliance", "accessibility_review", "api_compatibility"} <= ids(c, "selected_policies"), "C missing design policies")
    require(not ({"hilt_android", "baseline_profiles", "macrobenchmark"} & source_ids(c)), "C loaded unrelated DI/performance sources")
    require(c["context_budget"]["status"] in {"within_budget", "mandatory_context_exceeds_limit"}, "C has invalid context budget status")
    cases.append(("C Entire Material Design System", c))

    # D: Hilt only; no irrelevant visual/design context.
    d = route("Review dependency injection using Hilt.")
    require("hilt_android" in source_ids(d), "D missing official Hilt guidance")
    require({"architecture_boundaries", "dependency_selection"} <= ids(d, "selected_policies"), "D missing architecture policy")
    require(not ({"material3_site", "material_motion", "material_shape_principles", "figma_m3_kit"} & source_ids(d)), "D selected unrelated design context")
    cases.append(("D Hilt Architecture", d))

    # E: benchmark/profile references with no performance claim.
    e = route("Investigate Android startup performance.")
    require({"macrobenchmark", "baseline_profiles"} <= source_ids(e), "E missing benchmark/profile references")
    require("measurement_first" in ids(e, "selected_policies"), "E missing measurement-first policy")
    require(not any("improvement" in x.lower() or "faster" in x.lower() for x in e["required_verification_actions"]), "E claims a performance improvement")
    cases.append(("E Performance", e))

    # F: Roborazzi with NIA examples and explicit approval/evidence; no Figma.
    f = route("Establish screenshot regression testing using Roborazzi.")
    require({"roborazzi", "nia_screenshots"} <= source_ids(f), "F missing screenshot sources")
    require({"visual_baseline_approval", "testing_evidence"} <= ids(f, "selected_policies"), "F missing approval/evidence policy")
    require(not {"figma_theme_builder", "figma_m3_kit", "figma_nia_case_study"} & source_ids(f), "F loaded optional Figma references")
    cases.append(("F Visual Regression Testing", f))

    # G: selected Figma kit is blocked and has an explicit handoff; no token extraction.
    g = route("Extract design tokens from the Material 3 Figma Design Kit.")
    require("figma_m3_kit" in source_ids(g), "G missing Material 3 Design Kit reference")
    require(not ({"figma_theme_builder", "figma_nia_case_study"} & source_ids(g)), "G selected unrelated Figma references")
    require("material3_tokens" in {t["id"] for t in g["material3_topics"]}, "G missing relevant Material token topic")
    missing = g["missing_or_inaccessible_context"]
    require(any(x.get("source_id") == "figma_m3_kit" and x.get("status") == "blocked_403" for x in missing), "G did not report the access failure")
    require(any("export" in x["required_action"].lower() for x in missing), "G missing authorized export path")
    require(any("no numeric token" in x.get("detail", "").lower() for x in missing), "G failed to mark token values unextracted")
    require("knowledge/integrations/figma-workflow.md" in {x["path"] for x in g["selected_knowledge_references"]}, "G missing Figma handoff note")
    cases.append(("G Figma Access Failure", g))

    # H: newest/experimental API requires verification and makes no signature claim.
    h = route("Implement the newest experimental Expressive API.")
    require("api_compatibility" in h["classification"]["matched_domains"], "H API verification route did not match")
    require({"api_compatibility", "experimental_api", "no_hallucinated_api"} <= ids(h, "selected_policies"), "H missing required safeguards")
    require(any("target dependency" in action.lower() or "target artifact" in action.lower() for action in h["required_verification_actions"]), "H missing version check")
    require("fun expressive(" not in json.dumps(h).lower(), "H fabricated an API signature")
    cases.append(("H Unverified AndroidX API", h))

    # I: harness-only context stays away from app implementation routes.
    i = route("Improve Android context routing.")
    require(i["classification"]["matched_domains"] == ["harness_only"], "I failed to classify a harness-only task")
    require(not ({"compose_ui", "material3_expressive", "material_motion", "performance"} & set(i["classification"]["matched_domains"])), "I selected Android app implementation context")
    require("scope_isolation" in ids(i, "selected_policies"), "I missing scope isolation")
    require(not any(x["id"] in {"hilt_android", "roborazzi", "macrobenchmark"} for x in i["selected_sources"]), "I selected app implementation source")
    cases.append(("I Harness-Only Task", i))

    # J: unknown input stays conservative; broad Compose-only requests ask for clarification.
    j = route("Improve the thing.")
    require(j["classification"]["status"] == "unknown" and not j["classification"]["matched_domains"], "J invented an Android classification")
    require(not j["selected_sources"] and not j["selected_skills"] and not j["selected_knowledge_references"], "J loaded Android-specific context")
    broad = route("Compose")
    require(broad["classification"]["status"] == "ambiguous", "broad Compose request did not request clarification")
    material_broad = route("Material 3")
    require(material_broad["classification"]["status"] == "ambiguous" and not material_broad["selected_sources"], "broad Material request should not invent a topic")
    cases.append(("J Unknown and Ambiguous", j))

    # K: multiple domains merge policies and de-duplicate all selected identifiers.
    k = route("Review Compose navigation accessibility and screenshot testing.")
    require({"compose_ui", "material3_navigation", "material3_accessibility", "screenshot_testing"} <= set(k["classification"]["matched_domains"]), "K did not select all requested domains")
    for key in ("selected_sources", "selected_skills", "selected_policies", "selected_knowledge_references"):
        values = [x["id"] if key != "selected_knowledge_references" else x["path"] for x in k[key]]
        require(len(values) == len(set(values)), f"K duplicated entries in {key}")
    require("visual_baseline_approval" in ids(k, "selected_policies"), "K missing screenshot policy")
    require(not ({"hilt_android", "baseline_profiles", "macrobenchmark", "figma_m3_kit"} & source_ids(k)), "K loaded unrelated context")
    cases.append(("K Multi-Domain Task", k))

    # Deterministic output for identical task, registry, date, and budget.
    x1 = route("Implement animated MaterialShapes in Compose.", 24000)
    x2 = route("Implement animated MaterialShapes in Compose.", 24000)
    require(json.dumps(x1, sort_keys=True) == json.dumps(x2, sort_keys=True), "identical inputs produced different output")

    # Budget overflow retains complete references and explicitly reports the condition.
    tiny = route("Implement Material 3 Expressive motion in Jetpack Compose.", 1)
    require(tiny["context_budget"]["status"] == "mandatory_context_exceeds_limit", "tiny context budget did not report overflow")
    require("No arbitrary truncation" in tiny["context_budget"]["strategy"], "budget overflow could silently truncate required warnings")
    require(tiny["selected_knowledge_references"], "budget overflow silently removed required knowledge")

    # Direct identifier matching and inaccessible-source behavior.
    identifier = route("Use MotionScheme and MaterialShapes in Compose.")
    require({"material_motion", "material_shapes"} <= set(identifier["classification"]["matched_domains"]), "technical identifiers did not match")
    punctuated = route("Use Material-Shapes in Compose.")
    require(any(x["match_method"] == "technical_identifier" for x in punctuated["classification"]["match_evidence"]), "punctuated technical identifier matching failed")
    require(any(x.get("kind") == "live_verification_not_performed" for x in identifier["missing_or_inaccessible_context"]), "router overstated freshness/verification")

    print(f"PASS: {len(cases)} scenario groups (A-K), including unknown/ambiguous, determinism, budget, and identifier checks.")
    schema = json.loads((ROOT / "routing/context-manifest.schema.json").read_text(encoding="utf-8"))
    required_manifest_fields = set(schema["required"])
    required_global = {"security", "provenance", "scope_isolation", "source_access", "reporting", "testing_evidence"}
    for label, manifest in cases:
        require(required_manifest_fields <= set(manifest), f"{label}: output schema incomplete")
        require(required_global <= {p["id"] for p in manifest["selected_policies"]}, f"{label}: global mandatory policy omitted")
        require(all(s["activation"] == "recommended_not_activated" for s in manifest["selected_skills"]), f"{label}: router overclaims native skill activation")
        print(f"PASS: {label}: {manifest['routing_status']} ({len(manifest['selected_sources'])} sources, {len(manifest['selected_knowledge_references'])} knowledge refs)")
    print("PASS: repeated manifest output is byte-equivalent after stable JSON serialization.")
    print("PASS: budget overflow preserves whole required references and reports the limit.")
    print("PASS: source limitations and live-verification gaps are surfaced, never fabricated.")


if __name__ == "__main__":
    try:
        run()
    except (AssertionError, KeyError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
