# Optional Figma-to-Compose handoff

Figma is an optional design-input path, not a build/runtime dependency. The three supplied Figma URLs returned proxy HTTP 403; no plugin UI, file layers, assets, or design tokens were inspected. Do not invent colors, dimensions, typography, or component states from their titles.

When a designer supplies authorized access, record the file/page and revision, export or transcribe approved semantic color roles, typography styles, spacing/dimensions, shape values, component variants/states, and target-screen references. Keep the export (or a human-authored token table) alongside its provenance and approval. Map semantic roles to Compose `ColorScheme`, text styles to `Typography`, shape tokens to `Shapes`/component shapes, and dimensions to a centralized token source; document values that lack direct platform equivalents. Validate screenshots against only approved references and preserve the reference separately from generated candidates.

**Provenance:** `figma_theme_builder`, `figma_m3_kit`, and `figma_nia_case_study`; each blocked with HTTP 403. This workflow is a future handoff procedure, not extracted Figma content.
