# Deterministic context routing contract

## Invocation and boundaries

```bash
python3 scripts/route_context.py "Implement Material 3 Expressive motion in Jetpack Compose." --as-of 2026-10-14
```

`scripts/route_context.py` is a local Python standard-library keyword router. It reads the source, skill, policy, and taxonomy JSON, plus the Material topic manifest. It performs Unicode NFKC/casefold normalization, punctuation-to-space matching, and compact matching for technical identifiers. It fetches no network resources and runs no Android build. The same task, registry, budget, and `--as-of` date produce the same JSON manifest. When `--as-of` is omitted the current UTC date is used; set it to reproduce a saved route.

`routing/task-taxonomy.json` is the executable rule configuration. Each category has deterministic terms, bounded source IDs, knowledge paths, skill IDs, policy IDs, freshness/evidence requirements, exclusions, and optional route suppression. Sources are not selected by a blanket “all Android” fallback. Registry metadata supplies authority, access limitations, last-verification dates, version sensitivity, and source-task context for each selected reference.

## Manifest fields

Output schema version 1 includes the input and normalized task; classification status, domains and exact matching terms; selected sources with canonical URLs, authority and retrieval status; complete local knowledge paths; recommended skills and policy IDs; required verification actions; registry-age and live-verification status; inaccessible context; Material topic links; explicit exclusions; routing status; context-budget estimates; and `skill_execution_evidence`.

Skill entries say `recommended_not_activated`. The manifest records repository file presence and recommendation, while native discovery, invocation, session reads, and live freshness remain explicitly unobserved by the router. It contains local references, not document bodies, and does not claim Codex has read any selected file. Validate a saved manifest against the published JSON Schema with `python3 scripts/validate_context_manifest.py <file>`. Selected Markdown notes are concise provenance-bearing context. The budget estimates selected knowledge-note and policy-summary characters; potential native skill instruction size is reported separately. Required content is never arbitrarily truncated. If required notes exceed the budget, the manifest reports `mandatory_context_exceeds_limit` and keeps the references intact.

Statuses distinguish `routed`, `routed_with_limitations`, `ambiguous_clarification_recommended`, and `uncertain_no_domain_match`. Registry dates only establish age against a configurable review window. No live source/API check occurs during routing; version-sensitive sources require a separate check before implementation.

## Material 3 topic coverage

`routing/material3-topics.json` classifies Material.io design references separately from AndroidX implementation references. It covers foundations/Expressive, color, typography, shape, motion, layout, adaptive design, the full sitemap-listed component catalog, states, interaction, accessibility, tokens, navigation, spacing/density, elevation, iconography, content design, watch, and XR topics. `routing/material3-sitemap-evidence.json` stores the retrieved official sitemap URL subset and provenance, allowing validation that each declared Material page URL came from the sitemap.

On 2026-10-14 the sitemap returned HTTP 200 and contained 3,567 URLs; the harness recorded 249 URLs under `/foundations/`, `/styles/`, and `/components/`, excluding `/v0/` and editorial paths. Sitemap presence proves URL discovery only. The listed topic page bodies were not comprehensively retrieved; the site and some style pages returned a JavaScript shell. The manifest and route report that limitation and require live page review before page-specific design claims. AndroidX references such as `ColorScheme`, `Typography`, `MotionScheme`, `MaterialShapes`, and Compose adaptive/accessibility guides are separately typed implementation sources.

Figma remains an optional design handoff. A blocked file route returns its reference, access status, and export requirement without design tokens.

## Codex workflow

1. Run the router for the actual task and retain its output for review; validate it against the context-manifest schema.
2. Let native Codex skill discovery operate from the project skill files. When activation cannot be observed, explicitly read only the recommended skill files and report this as a read, not an invocation.
3. Read only selected knowledge notes and policies; record actual reads separately from selection.
4. Inspect selected official sources when the manifest requests freshness checks; validate the target project's resolved API/version.
5. Apply mandatory global and selected task policies.
6. Execute relevant project checks and record results. The router itself never treats an unexecuted check as PASS.

Validate router rules and scenario behavior with `python3 evals/run_context_router_evals.py` and skill selection with `python3 evals/run_skill_integration_evals.py`; validate registries and skill metadata with their `scripts/validate_*.py` checks.
