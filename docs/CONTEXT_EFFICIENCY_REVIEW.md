# Context selection efficiency review

## Scope and reproducibility

The evaluation compares the committed router at `f700ca6197dfad5da12546fc2767b44b534d041b` with the P12 working tree, using the same task, registry snapshot, and frozen date (`2026-10-15`). It measures router output and referenced local content; it does not measure what a Codex model actually consumed.

Primary narrow task: `Add a narrow Compose accessibility test for screen reader semantics.` Contrasting tasks cover Material 3 Expressive UI, Compose performance, generic visual design review, and combined Material 3 plus accessibility testing. Run `python3 evals/run_context_efficiency_evals.py` to replay all five cases.

## Narrow-task selection

| Context item | Before | After | Decision |
| --- | --- | --- | --- |
| Sources | Compose accessibility guidance, Android Skills, Material.io, AndroidX Material 3 | Compose accessibility guidance and Android Skills | Keep the implementation/test sources; omit unrelated Material design authorities. |
| Skills | `android-testing`, `kotlin-compose`, `material3-expressive`, `visual-design-validation` | `android-testing`, `kotlin-compose` | Keep the two directly applicable skills. Material and rendered-design review remain discoverable when explicitly requested. |
| Knowledge | 3 references / 3,009 chars | `knowledge/androidx/compose-accessibility.md` / 1,161 chars | Keep the Compose semantics/test note. Exclude generic Material notes whose page bodies are unverified and not required for a test-only task. |
| Policies | 11 policies / 1,105 summary chars | 10 policies / 1,015 summary chars | Keep all eight mandatory global policies plus `accessibility_review` and `api_compatibility`; omit unrelated `design_compliance`. |
| Selected-content estimate | 4,114 chars | 2,176 chars | Knowledge plus policy summaries only; skill bodies and manifest metadata are reported separately. |
| Pretty JSON manifest | 20,268 bytes/chars | 11,527 bytes/chars | Same CLI serialization, including its trailing newline. |
| Inline unverified Material.io URLs | 25 URLs (the topic had 40 discovered) | 0 for this task | The Material domain is not applicable here. On relevant Material tasks the manifest reports a count and `routing/material3-topics.json` pointer, not a repeated URL dump. |

Manifest output fell by 8,741 bytes (43.1%). Recommended skill-file size, if both sets of recommendations were actually read, fell from 6,377 to 2,965 chars; this is conditional size, not observed reading. Selected local knowledge fell by 1,848 chars (61.4%), selected policy summaries by 90 chars (8.1%), and the router's selected-content estimate by 1,938 chars (47.1%). The two task-specific policies remain, while eight global mandatory policies remain non-removable.

These are measured character/byte counts, not model-token counts. Token count is **NOT VERIFIED**. The router says a file is selected/recommended; it does not prove the file was opened, a native skill was invoked, or its text entered model context.

## Routing decisions and exclusions

- **Compose accessibility test only:** selects `compose_accessibility_testing` plus general Compose testing. Keeps `android-testing`, `kotlin-compose`, AndroidX Compose accessibility knowledge, accessibility/API checks, and mandatory global policies. Excludes Material 3, visual-design validation, and performance context.
- **Material 3 Expressive UI:** keeps Material topic routes, `material3-expressive`, AndroidX implementation/version checks, and relevant accessibility/design guidance. It reports the Material.io page-content limitation rather than treating discovered links as verified evidence.
- **Compose performance optimization:** keeps Android performance and Compose performance skills/knowledge with measurement-first requirements. Excludes Material design and visual-review context.
- **Generic visual design review:** keeps the visual-validation skill and manual design-compliance contract. It does not select Material 3 references unless the request names Material design/components.
- **Combined accessibility and Material 3 UI:** merges both domains and retains design, accessibility, API compatibility, and global policies without duplicate IDs.

Conditional exclusions are declarative per route. They remove only the named domain's contribution; when another independently matched task domain needs the same policy, skill, or reference, that selection is retained. The global mandatory policy set is not subject to minimization.

## Validation evidence

`evals/run_context_efficiency_evals.py` asserts positive and negative source, skill, knowledge, and policy selection for all five tasks, checks mandatory policies, and replays an identical task to verify deterministic output. Registry validation checks the conditional-exclusion references. Bootstrap and P2–P11 regressions exercise the wider router and harness behavior.

**NOT VERIFIED:** no independent Android engineering A/B outcome, model-token measurement, actual native skill invocation, or selected-file consumption is established by these routing tests. Live Material.io page verification remains at its evidence-backed value; reducing irrelevant links does not change that status.
