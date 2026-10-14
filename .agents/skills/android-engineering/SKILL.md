---
name: android-engineering
description: Change the Android context harness, evaluate task routing, or prepare repository context for a future Android task.
---

# Android context engineering

## Scope
Harness routing, context selection, source provenance, skill selection and harness-only changes. Android application architecture belongs to `compose-architecture`.

## Preconditions and required context selection
For a task in this repository, inspect its `AGENTS.md`, then run `python3 scripts/route_context.py "<task>" --as-of YYYY-MM-DD`. Validate the JSON manifest with the declared schema and consult only its selected knowledge and policy references. The router is deterministic metadata, not a skill loader or source fetcher.

## Knowledge and policies
Read `knowledge/codex/iterative-workflows.md`, `knowledge/android-skills/codex-integration.md`, and `docs/CONTEXT_ROUTER.md` when relevant. Always apply global security, provenance, scope, source access, freshness, no-hallucinated-API, testing evidence and reporting policies from the manifest.

## Applicable policy IDs
`security`, `provenance`, `scope_isolation`, `source_access`, `reporting`, `freshness`, `no_hallucinated_api`, `testing_evidence`.

## Workflow
Inspect → Plan → Implement → Validate → Review → Report. Preserve Material 3 topics/sitemap evidence; do not fetch sources unless the environment policy permits it. Harness-only work must not create an Android app, APK/AAB, Gradle project, or Compose UI.

## Verification
Run registry and P2/P3 evaluations after routing changes. Report exact commands, outcomes, and unavailable evidence.

## Failure and uncertainty
Separate skill file presence, Codex-native discovery, recommendation, invocation, file reading and live freshness checks. Record only observed evidence. Treat unknown task classification, blocked pages and stale registry dates as unresolved; never infer unavailable source contents or report unrun checks as PASS.
