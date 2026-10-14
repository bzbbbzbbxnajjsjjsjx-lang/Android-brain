# Material motion decisions

Select motion to communicate a state change, spatial relationship, or hierarchy. Match the transition to the content and input; keep duration and distance proportional, avoid motion that delays task completion, and respect reduced-motion/accessibility settings. Test state changes and interruption, not only a looping preview. Consider recomposition and frame cost, but require device measurements before performance claims.

The supplied Material motion page returned only its JavaScript shell, so no detailed motion taxonomy is attributed to it here. Before implementation, verify the Compose transition API and any Material `MotionScheme` availability, artifact version, stability/experimental annotation, and reduced-motion behavior from current AndroidX documentation/source. Never translate View animators directly into Compose APIs.

**Provenance:** `material_motion` (partial page access); `material_shapes_api` (AndroidX API source); `legacy_view_motion` (legacy boundary).
