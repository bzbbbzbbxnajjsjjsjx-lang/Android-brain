# Material 3 Expressive API verification

Relevant official API entry points include the Material3 package summary, `MaterialTheme`, `ColorScheme`, `Typography`, `MotionScheme`, and `MaterialShapes`. These references describe API surfaces; they do not by themselves prove a symbol exists in the artifact resolved by a particular project.

Before using an Expressive component, `MaterialShapes`, morphing, `MotionScheme`, or theme role:

1. Inspect the target project's resolved Material3 artifact and Compose BOM/runtime/UI versions.
2. Check the matching official reference and published source JAR for the exact symbol, visibility, signature, and opt-in annotation.
3. Check POM constraints and transitive compatibility; do not infer compatibility from a newer reference page.
4. If experimental, keep opt-in narrow and document the migration risk. Build and test against the actual project.

P0 evidence (2026-10-14): official package, MaterialTheme, ColorScheme, Typography, MotionScheme, and MaterialShapes HTML bodies were fetched and relevant excerpts inspected. The current reference describes `MotionScheme.expressive()` and `standard()`, exposes `MaterialTheme.motionScheme`, and marks `MaterialShapes` with `@ExperimentalMaterial3ExpressiveApi`. These current-reference observations do not establish availability in an arbitrary target artifact. Google Maven metadata listed Material3 `1.5.0-beta01`; its POM requires Compose UI/runtime `1.12.0`. Selected published `1.5.0-alpha01` sources exposed relevant Expressive APIs behind `@ExperimentalMaterial3ExpressiveApi`; its POM minimums and BOM pairing were investigated for the previous app task. This is historical research evidence, not a recommendation to pin those versions in future repositories. Stable `1.4.0` did not expose the studied expressive surface publicly. Recheck all facts when choosing a target project's versions.

**Provenance:** `material_shapes_api`, `androidx_material3_package`, `androidx_material_theme`, `androidx_motion_scheme`, `androidx_color_scheme`, `androidx_typography`; Google Maven metadata and published source/POM retrieval noted in P0 audit. Exact availability can change after registry verification.
