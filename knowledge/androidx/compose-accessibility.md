# Compose accessibility implementation reference

The official Android Developers guide describes Compose accessibility through API defaults, semantics, traversal order, scalable content, merging or clearing semantics, inspection/debugging, and testing. Use semantic labels, roles, state, and actions to convey meaning to accessibility services, particularly for custom controls. Review traversal order and grouping when the visual layout does not provide a useful reading sequence. Keep content usable at larger text scales and test the rendered result; automated semantics checks and tools help find defects but do not replace assistive-technology review.

This is implementation guidance from Android Developers, not a Material.io component specification. Verify current APIs and component semantics against the target project and combine automated checks with manual review.

**Provenance:** `androidx_compose_accessibility`, official Android Developers guide. Actual page-body retrieval and inspected sections are recorded in `routing/google-android-retrieval-evidence.json` (2026-10-14). Source availability does not itself verify an app's accessibility.
