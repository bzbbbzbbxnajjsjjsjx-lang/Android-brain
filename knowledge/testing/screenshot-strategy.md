# Screenshot regression strategy

Treat approved reference images as reviewed source assets. Capture deterministic fixtures across a purposeful screen-size/theme/font-scale/state matrix; include loading, empty, error, selected, pressed, and disabled states when those states exist. Version-control baselines with provenance and renderer/device configuration. Separate generated candidates from approved references and require explicit human review for baseline updates. A comparison must fail for a deliberate visual change before trusting it.

Roborazzi is a community screenshot tool; verify Android Gradle Plugin, Compose, Robolectric, and renderer compatibility before adoption. Keep behavior/accessibility tests separate from pixel comparison. NIA's supplied screenshot directory listing exposed compact/medium/expanded and snackbar/insets examples; images were not adopted as baselines. Figma targets require approved accessible exports.

**Provenance:** `nia_screenshots` (metadata listing only), `roborazzi` (README/POM), `figma_*` (blocked, handoff only).
