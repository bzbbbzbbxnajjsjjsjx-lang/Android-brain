# P5 evaluation methodology

## Independent routing dataset

`evals/datasets/context_tasks.v1.json` is version 1 of a human-authored set of 40 requests. Expected domains, required and allowed context, forbidden sources, required skills/policies, freshness checks, route status, and evidence actions are specified per case rather than generated from `routing/task-taxonomy.json`. It covers all 21 Material 3 topic groups plus AndroidX APIs, architecture, testing, performance, Figma limits, ambiguous/unknown requests, negative mentions, and harness-only work. Router metrics are calculated from actual manifests. Every task failure remains visible; aggregate scores do not suppress it.

Metrics use set overlap. Required-source/skill/knowledge recall is selected-required divided by required; precision is selected relevant (required or explicitly allowed optional) divided by selected, with empty selections scored 1 only when there is no expected relevant context. Exact classification compares the full matched-domain set. Policy coverage requires the union of dataset-global mandatory and case-required policy IDs. Forbidden-source rate counts selections explicitly forbidden by that case. Determinism compares canonical JSON for two executions of each same request. Context size is selected local knowledge and policy characters, not tokens; native skill activation and their full instruction bodies are not controlled or counted exactly by the router.

The thresholds are fixed in the runner before measurement: exact domains >= 0.90; required source recall >= 0.95; source precision >= 0.80; skill recall >= 0.90; skill precision >= 0.80; knowledge recall >= 0.90; knowledge precision >= 0.75; policy coverage == 1; zero forbidden sources; every case deterministic; all 21 Material topics and all 249 discovered sitemap URLs categorized. Each case must also pass all of its own assertions. These thresholds are evaluation gates, not a claim of release readiness.

## Adversarial and mutation checks

`evals/run_adversarial_evals.py` tests explicit negation, mixed-domain policy de-duplication, a one-character context budget, stale source dates, an inert local prompt-injection fixture, evidence digest/result contradictions, and the distinction between skill metadata discovery and invocation. Quality-gate decisions are delegated to the existing P4 evaluator. The fixture contains hostile text but is never fetched from a live source or executed; no model run is involved, so this verifies the harness contract, not LLM resistance.

`evals/run_mutation_evals.py` copies the repository to temporary directories and injects eleven faults, including duplicate IDs, broken local/provenance references, weakened mandatory policy, API misclassification, missing Material coverage, and irrelevant source contamination. Structural mutations are sent through the registry validator; source contamination and Figma accessibility mutations are tested against independent task expectations. No mutation is applied to the primary checkout. A changed route that remains structurally valid must still be caught by task-level expected outcomes.

## Material.io evidence boundary

The separate URL-coverage result counts registered topic groups and sitemap URLs. It does not measure page content. Current manifest state: 21 topic groups cover all 249 URLs; 0 topics have individually verified page content, and all 21 remain `CONTENT NOT VERIFIED`. Do not interpret discovery through a sitemap as specification review. AndroidX APIs, Figma assets, Material.io guidance, community tools, and legacy View documentation remain distinct source classes.

## Reproduction

```bash
python3 scripts/validate_registry.py
python3 scripts/validate_skills.py
python3 evals/run_context_router_evals.py
python3 evals/run_skill_integration_evals.py
python3 evals/run_quality_gate_evals.py
python3 evals/run_harness_evals.py --output /tmp/p5-routing-report.json
python3 evals/run_adversarial_evals.py
python3 evals/run_mutation_evals.py
```

The standard-library router does not fetch sources. Current-source verification, live CI, native skill invocation/body consumption, Android build behavior, and authenticated evidence are outside this local suite unless independently observed and recorded. A successful local evaluation does not establish hosted CI. The P5 result JSON is a local measurement report, not a signed artifact.

## Repository integrity caveat

At P5 start the work branch had no commit/HEAD and `git ls-files` returned zero tracked files; all existing project files were untracked. This makes conventional change review and reproducible release lineage unavailable. No files were cleaned, committed, pushed, or history-rewritten. Before release, an authorized maintainer must establish or restore the intended repository baseline and review/commit the harness through the normal project process. The evaluator does not declare repository release readiness.
