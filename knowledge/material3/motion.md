# Material motion knowledge access status

The registered Material.io motion URL returned a JavaScript shell; its article content and motion taxonomy were not retrieved or verified. This note therefore provides no Material-specific motion rules. Do not derive durations, easing, transition choices, or reduced-motion behavior from the URL or shell.

For Compose implementation, verify the actual transition API, any `MotionScheme` availability and opt-in, and reduced-motion behavior against current official AndroidX documentation and the target artifact. Do not transplant View animation APIs into Compose. Measure device performance before making performance claims.

**Provenance:** `material_motion` (shell only); `androidx_motion_scheme` and `androidx_material3_package` (separate, version-sensitive implementation references); `legacy_view_motion` (View-system documentation, not a Compose recipe).
