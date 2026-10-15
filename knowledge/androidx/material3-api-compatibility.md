# Material 3 Expressive API verification

Relevant official API entry points include the Material3 package summary, `MaterialTheme`, `ColorScheme`, `Typography`, `MotionScheme`, and `MaterialShapes`. These references describe API surfaces; they do not by themselves prove a symbol exists in the artifact resolved by a particular project.

Before using an Expressive component, `MaterialShapes`, morphing, `MotionScheme`, or theme role:

1. Inspect the target project's resolved Material3 artifact and Compose BOM/runtime/UI versions.
2. Check the matching official reference and published source JAR for the exact symbol, visibility, signature, and opt-in annotation.
3. Check POM constraints and transitive compatibility; do not infer compatibility from a newer reference page.
4. If experimental, keep opt-in narrow and document the migration risk. Build and test against the actual project.

P0 evidence (2026-10-14): official package, MaterialTheme, ColorScheme, Typography, MotionScheme, and MaterialShapes HTML bodies were fetched and relevant excerpts inspected. The current reference describes `MotionScheme.expressive()` and `standard()`, exposes `MaterialTheme.motionScheme`, and marks `MaterialShapes` with `@ExperimentalMaterial3ExpressiveApi`. These current-reference observations do not establish availability in an arbitrary target artifact. Google Maven metadata listed Material3 `1.5.0-beta01`; its POM requires Compose UI/runtime `1.12.0`. Selected published `1.5.0-alpha01` sources exposed relevant Expressive APIs behind `@ExperimentalMaterial3ExpressiveApi`; its POM minimums and BOM pairing were investigated for the previous app task. This is historical research evidence, not a recommendation to pin those versions in future repositories. Stable `1.4.0` did not expose the studied expressive surface publicly. Recheck all facts when choosing a target project's versions.

P8 re-retrieval evidence (2026-10-14) is recorded in `routing/google-android-retrieval-evidence.json`. The current official `MaterialTheme`, `ColorScheme`, and `Typography` pages were separately retrieved and inspected. `MaterialTheme` reference text exposes theme properties including color scheme, typography, shapes, and the current motion scheme property. `ColorScheme` documents named semantic roles and constructors; `Typography` documents reusable text roles and the current page includes version-annotated additional overloads. These are descriptions of the retrieved reference, not a claim that every item exists in a project's resolved dependency. Do not copy a signature or select a minimum version from this note; compare the target artifact's official API and source.

**Provenance:** `material_shapes_api`, `androidx_material3_package`, `androidx_material_theme`, `androidx_motion_scheme`, `androidx_color_scheme`, `androidx_typography`, `androidx_compose_material3_guide`; Google Maven metadata and published source/POM retrieval noted in P0 audit. P8 response/extracted text hashes are in the separate Google Android evidence file. Exact availability can change after registry verification.
