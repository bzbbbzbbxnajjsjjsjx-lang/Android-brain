---
name: android-performance
description: Measure Android startup or interaction performance, or investigate a bottleneck supported by repeatable evidence.
---

## Scope
Android startup/interaction benchmark strategy, Macrobenchmark and Baseline Profile readiness. Compose-specific bottlenecks may also require the official `jetpack-compose-performance` skill.

## Preconditions and required context selection
Run the context router and read `knowledge/performance/measurement.md` plus selected official performance references. Inspect app/build type, benchmark module, device/OS, and profile generation prerequisites.

## Applicable policy IDs
`measurement_first`, `performance_claims`, `dependency_selection`, `freshness`, `testing_evidence`.

Use release-like builds and repeatable workloads where supported.

## Workflow
Establish a comparable baseline before optimization. Add Baseline Profile generation only after suitable benchmark infrastructure works. Change one relevant factor at a time and rerun the same workload/environment.

## Verification
Report build variant, device/OS, workload, benchmark iterations and baseline/comparison results. Separate measured facts from hypotheses.

## Failure and uncertainty
Do not claim gains from static inspection, host rendering, recomposition counts or unexecuted benchmarks. If device/benchmark infrastructure is unavailable, state BLOCKED and provide no performance-improvement claim.
