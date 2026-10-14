---
name: compose-architecture
description: Review or change Jetpack Compose architecture, state ownership, Hilt dependency injection, modularization, or Android build variants.
---

## Scope
Android application architecture for Compose-based code. This covers state boundaries, data flow, Hilt, modularization and product flavors without prescribing a fixed module count.

## Preconditions and required context selection
Run the context router and read only selected architecture/Hilt/build-variant notes. Inspect the actual repository, resolved plugin/library versions, existing DI and module boundaries first.

## Applicable policy IDs
`architecture_boundaries`, `scope_isolation`, `dependency_selection`, `api_compatibility`, `security`, `testing_evidence`.

## Workflow
Keep UI state and events testable and lifecycle-aware. Use Now in Android as a reference, not a template. Add Hilt only when its graph and testing benefits justify its maintenance; modularize only for demonstrated ownership, build, reuse or isolation needs; introduce flavors only for real product/configuration differences.

## Verification
Check dependency graph/build configuration against official current guidance. Run relevant compilation, unit/Compose tests and variant-specific checks that exist in the target project.

## Failure and uncertainty
Do not infer module structure or dependency versions. If architecture or build constraints are unavailable, identify them before proposing changes. Mark unexecuted checks NOT VERIFIED; do not claim production readiness from a design review.
