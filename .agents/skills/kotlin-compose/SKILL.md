---
name: kotlin-compose
description: Implement Jetpack Compose UI behavior, state, semantics, layouts, or rendering after architectural boundaries are established.
---

## Scope
Compose UI behavior and state implementation. Use `compose-architecture` for state ownership, module boundaries, dependency injection, or build variants; use `material3-expressive` for Material design rules and Material 3 components.

## Preconditions and required context selection
Run the repository's context router first. Read only selected AndroidX notes and official `edge-to-edge` skill guidance when the task touches system bars or insets. Inspect the target project's Compose version and existing conventions before changing code.

## Applicable policy IDs
`api_compatibility`, `accessibility_review`, `dependency_selection`, `testing_evidence`, `scope_isolation`, `reporting`.

## Workflow
Keep state and events testable; prefer semantic components; check adaptive constraints. Follow Inspect → Plan → Implement → Build → Test → Observe → Review → Report.

## Verification
Verify symbols against the target project's resolved artifacts and current official reference. Execute behavior checks and inspect rendered output when a renderer exists.

## Failure and uncertainty
Do not infer API availability or visual quality from compilation. Mark unavailable device/render evidence BLOCKED or NOT VERIFIED, and do not claim an API signature without current source evidence.
