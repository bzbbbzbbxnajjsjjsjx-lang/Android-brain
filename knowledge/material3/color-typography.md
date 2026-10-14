# Material color and typography routing note

Material.io's sitemap lists color roles, schemes, dynamic color, typography, font selection, applying type, and type-scale tokens. The pages themselves were not inspected here, so no token values, contrast thresholds, or typography prescriptions are claimed from them. Retrieve the applicable Material pages or an approved design handoff before making design-specific decisions.

On Android, `ColorScheme` and `Typography` are Compose Material3 implementation surfaces, not the Material.io specification. Confirm the selected artifact and available roles/styles in the target project's official AndroidX reference and resolved sources. Map approved design semantics deliberately; do not invent role values from a Figma file the team cannot access.

**Provenance:** `material3_site` (sitemap-listed paths); AndroidX API sources `androidx_color_scheme`, `androidx_typography`, `androidx_material_theme`.
