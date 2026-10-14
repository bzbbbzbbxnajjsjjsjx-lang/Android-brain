---
name: material3-expressive
description: Design or implement Material Design 3 foundations, color, typography, shape, motion, layout, adaptive patterns, components, tokens, navigation, or accessibility in Compose.
---

## Scope
The complete Material 3 design domain, including all topic IDs in `routing/material3-topics.json`. Material.io supplies design principles, specifications and interaction guidance; AndroidX Compose supplies actual API signatures, artifacts and opt-in status. Figma is optional and only usable through accessible assets or an authorized export.

## Preconditions and required context selection
Run `python3 scripts/route_context.py "<task>" --as-of YYYY-MM-DD` and select the matching Material topics, notes, sources and policies from its manifest. Do not load all 249 sitemap URLs into this skill. Read `knowledge/material3/*` notes only when selected; inspect selected Material.io pages before making page-specific claims. Verify target dependency versions before relying on AndroidX API details.

## Applicable policy IDs
`design_compliance`, `accessibility_review`, `api_compatibility`, `experimental_api`, `source_access`, `provenance`, `visual_baseline_approval`.

## Workflow
Map design intent to the relevant Material topic, then map implementation to verified AndroidX Compose APIs. Check roles, states, interaction, typography, contrast, text scaling, adaptive behavior and component semantics as applicable. Keep motion state-driven and shapes purposeful.

## Verification
Run build and behavior checks; inspect rendered output when available.

## Failure and uncertainty
Material sitemap discovery establishes URL coverage, not page-body review. Label inaccessible/JS-shell content unverified. Never invent API signatures, compatibility, design rules or Figma tokens. Mark blocked retrieval, missing target versions, or absent render evidence explicitly.
