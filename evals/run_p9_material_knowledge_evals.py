#!/usr/bin/env python3
"""P9 regressions for official Material Components source provenance and routing."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import route_context
import validate_google_material_components_evidence as validator
import validate_material_evidence


def main() -> int:
    registry = json.loads((ROOT / "registry/sources.json").read_text())
    evidence = json.loads((ROOT / "routing/material-components-android-evidence.json").read_text())
    topics_doc = json.loads((ROOT / "routing/material3-topics.json").read_text())
    topics = topics_doc["topics"]
    result = validator.validate(evidence, registry, topics)
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append((name, bool(ok), detail))
        if not ok:
            raise AssertionError(f"{name}: {detail}")

    check("google_owned_pinned_sources", result["verified_view_documents"] == 11 and all(
        row["canonical_url"].startswith("https://github.com/material-components/material-components-android/blob/")
        and row["repository_revision"] == evidence["repository_revision"]
        for row in evidence["records"]
    ), "Eleven body-hash records point to official Google-owned source documents at a pinned revision.")
    check("source_family_separation", all(row["source_family"] == "google_material_components_view_documentation" for row in evidence["records"])
          and json.loads((ROOT / "routing/material3-retrieval-evidence.json").read_text())["records"]
          and len(topics) == 21, "Material Components View documents remain separate from Material.io page evidence and the 21-topic taxonomy.")
    check("sitemap_discovery_not_content_verification", len(json.loads((ROOT / "routing/material3-sitemap-evidence.json").read_text())["urls"]) == 249
          and validate_material_evidence.validate_records(
              json.loads((ROOT / "routing/material3-retrieval-evidence.json").read_text()),
              topics,
              json.loads((ROOT / "routing/material3-sitemap-evidence.json").read_text())["urls"],
          )["verified_page_content_topics"] == 0,
          "The 249 discovered URLs do not upgrade Material.io's verified page-content count.")

    bad = copy.deepcopy(evidence)
    bad["records"][0]["canonical_url"] = "https://third-party.example/material"
    try:
        validator.validate(bad, registry, topics)
        rejected = False
    except ValueError:
        rejected = True
    check("third_party_or_misattributed_source_rejected", rejected, "Noncanonical third-party source attribution is rejected.")

    bad = copy.deepcopy(evidence)
    bad["records"][0]["source_family"] = "material_io_design_specification"
    try:
        validator.validate(bad, registry, topics)
        rejected = False
    except ValueError:
        rejected = True
    check("view_docs_cannot_claim_material_io", rejected, "A GitHub View document cannot be relabeled as inspected Material.io content.")

    compose = route_context.build_manifest("Implement Material 3 components in Jetpack Compose.")
    compose_sources = {row["id"] for row in compose["selected_sources"]}
    compose_refs = {row["path"] for row in compose["selected_knowledge_references"]}
    check("compose_excludes_view_xml_guides", not any(s.startswith("material_components_android_") for s in compose_sources)
          and not any(path.startswith("knowledge/material3-view/") for path in compose_refs)
          and any("legacy View/XML" in x for x in compose["explicit_exclusions"]["category_rules"]),
          "A Compose component task excludes legacy View/XML implementation notes and records the exclusion.")

    legacy = route_context.build_manifest("Review Material 3 components in existing View/XML MDC-Android.")
    legacy_sources = {row["id"] for row in legacy["selected_sources"]}
    legacy_refs = {row["path"] for row in legacy["selected_knowledge_references"]}
    check("explicit_view_request_selects_scoped_knowledge", {
        "material_components_android_status", "material_components_android_button_groups",
        "material_components_android_text_fields", "material_components_android_cards",
    } <= legacy_sources and all(path.startswith("knowledge/material3-view/") for path in legacy_refs if "material3-view/" in path),
          "An explicit View/XML request selects the pinned View library references only within the matched component topic.")
    check("legacy_compose_boundary_and_version_check", any("do not port" in x.lower() and "compose" in x.lower() for x in legacy["required_verification_actions"])
          and any("dependency" in x.lower() for x in legacy["required_verification_actions"]),
          "The route warns against porting legacy APIs and requires checking the existing dependency.")

    material_tasks = {
        "Material 3 color design": "material3_color",
        "Material 3 typography hierarchy": "material3_typography",
        "Material 3 component anatomy and states": "material3_components",
        "Material 3 navigation and adaptive layout": "material3_navigation",
        "Material 3 Expressive motion and shapes": "material_motion",
        "Material 3 accessibility guidance": "material3_accessibility",
        "Material 3 iconography and content design": "material3_content_design",
        "Material 3 elevation spacing and design tokens": "material3_tokens",
        "Material 3 wearable and XR design": "material3_xr",
    }
    routing_ok = True
    for task, topic in material_tasks.items():
        manifest = route_context.build_manifest(task)
        routing_ok &= topic in {item["id"] for item in manifest["material3_topics"]}
    check("material_topic_routing", routing_ok, "Representative Material 3 task prompts reach their registered topic groups.")

    color = route_context.build_manifest("Implement a Material 3 color system in Jetpack Compose.")
    check("androidx_version_verification_preserved", any("target project" in x.lower() and "dependency" in x.lower() for x in color["required_verification_actions"])
          and any(x["id"] == "androidx_compose_material3_guide" for x in color["selected_sources"]),
          "Compose implementation routes include official Android guidance and target-project version verification.")
    registry_hosts = {row.get("canonical_url", "").split("/")[2] for row in registry["sources"] if row.get("canonical_url", "").startswith("https://")}
    check("no_third_party_documentation_provider_added", "material-docs.example" not in registry_hosts
          and not any("documentation_mcp" in row["id"] for row in registry["sources"])
          and not any("mcp" in line.casefold() for line in (ROOT / "requirements-dev.txt").read_text().splitlines()),
          "No third-party documentation provider or MCP dependency was added.")
    first = route_context.build_manifest("Implement Material 3 components in Jetpack Compose.")
    second = route_context.build_manifest("Implement Material 3 components in Jetpack Compose.")
    check("manifest_determinism", json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True),
          "The same task and repository state produce identical logical context manifests.")

    print(f"P9 official Material knowledge evaluations {sum(ok for _, ok, _ in checks)}/{len(checks)} PASS")
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
