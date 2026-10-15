# Text fields (View library)

The guide separates filled and outlined View text fields and identifies container, label, input, indicator, icons, helper/error/counter content. Its View-specific accessibility section recommends meaningful labels/helper text, descriptions for actionable custom icons, an error description when error text is not pronounceable, and a TextInputLayout accessibility delegate for a custom child. These are observations about TextInputLayout/TextInputEditText, not Compose semantics.

## Scope and implementation boundary

This is documentation for the Google-maintained **Material Components for Android Views/XML library** at repository revision `60ff09436d5d477a4b9d02940f31eb01e1250620`. It is not a retrieved Material.io page, and it is not a Jetpack Compose API reference. Use it only when a task explicitly asks about existing View/XML MDC-Android code. For Compose, use the independently registered AndroidX API sources and verify the target project's resolved versions. The repository README at this same revision reports the View library in maintenance mode; check current project and migration context before applying legacy guidance.

## Provenance

- Source ID: `material_components_android_text_fields`
- Canonical URL: https://github.com/material-components/material-components-android/blob/60ff09436d5d477a4b9d02940f31eb01e1250620/docs/components/TextField.md
- Repository: https://github.com/material-components/material-components-android
- Pinned revision: `60ff09436d5d477a4b9d02940f31eb01e1250620`
- Retrieved and inspected: 2026-10-14 via HTTPS GET from `raw.githubusercontent.com`, TLS verification enabled.
- Inspected sections: filled and outlined variants, anatomy, error/helper/counter properties, Making text fields accessible, custom EditText.
- Body SHA-256: `6d15e624765ef5865c114582d1d2d6c6f8573d4076fb009e3bc44b64c13541aa`; evidence is in `routing/material-components-android-evidence.json`.
- License: upstream Apache-2.0; source summaries are original and do not reproduce the document.
- Limitation: the document links to Material.io but does not prove that linked page body was retrieved or verified.
