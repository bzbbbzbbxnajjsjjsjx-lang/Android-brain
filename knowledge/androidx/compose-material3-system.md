# Material 3 in Compose: implementation guidance

This note summarizes the **Android Developers implementation guide**, not the Material.io design specification. Material.io remains the design authority, and its page-content status is still unverified in this environment.

The guide describes Compose Material 3 theming as a coordinated `MaterialTheme` containing a color scheme, typography, and shapes; components consume those theme values by default. Keep product tokens centralized, and make a deliberate choice about light and dark schemes. The guide describes dynamic color as available on Android 12 and later, with custom light/dark schemes as the fallback. It presents five key colors with tonal palettes and explains that color roles should be chosen for component emphasis and state rather than treated as arbitrary paint values.

The documented type scale groups styles into display, headline, title, body, and label. Use roles consistently for hierarchy and customize only what the product needs. The guide describes the shape scale as a way to direct attention, identify components, communicate state, and express brand; theme-wide defaults and per-component overrides are both available implementation approaches.

Choose component variants according to action emphasis. Treat navigation choice as adaptive: the guide associates navigation bars with compact layouts and up to five destinations, rails with compact/landscape or smaller tablet layouts, and drawers with larger layouts. These are guide examples, not a substitute for current product-specific adaptive decisions. Material components provide defaults and customization surfaces for color/elevation; verify exact APIs against the target project's resolved artifact.

The guide describes Material 3 surface elevation as tonal overlays alongside shadow elevation. It also notes Android-version-dependent system ripple behavior and Compose Foundation overscroll behavior. Do not assume those details apply identically across every target dependency/API level.

## Implementation and compatibility boundary

This guide establishes implementation concepts and examples, not current compatibility for a consuming app. Before coding, inspect the target project's resolved Material 3 and Compose versions, consult the matching official AndroidX reference/release source, and verify exact symbols, signatures, and experimental opt-ins. The examples in a live guide may evolve. Do not infer an API or version from this note.

## Provenance and review evidence

- Source: `androidx_compose_material3_guide` — [Material Design 3 in Compose](https://developer.android.com/develop/ui/compose/designsystems/material3)
- Actual access: HTTPS GET returned HTTP 200 and a substantive rendered article body; an HTML `article` extraction was inspected locally. This was not a Material.io page retrieval.
- Reviewed sections: theming, color scheme, dynamic color, typography, shapes, emphasis, elevation, Material components, navigation components, component customization, system UI, accessibility.
- Retrieved: 2026-10-14. Response SHA-256: `b96e8ff0946f8ab83fa482a0a7d9f00b7b734b66cf138be7f0dcc9695ac4ac18`.
- Verification record: `routing/google-android-retrieval-evidence.json`.
- Limitations: the digest identifies the retrieved response but does not preserve it; it is not a signed archive or independent proof of content accuracy. Re-fetch and inspect relevant sections before relying on freshness-sensitive guidance.

**Related implementation references:** `androidx_material_theme`, `androidx_color_scheme`, `androidx_typography`, `androidx_material3_package`, and `androidx_compose_accessibility`. AndroidX references define actual API contracts; the target project's dependency compatibility remains a separate mandatory check.
