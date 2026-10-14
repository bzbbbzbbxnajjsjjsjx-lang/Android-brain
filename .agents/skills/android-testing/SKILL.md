---
name: android-testing
description: Plan or implement Android unit, Compose UI, instrumentation, screenshot, or visual regression tests.
---

## Scope
Android test strategy and evidence contracts; screenshot baseline governance is coordinated with `visual-design-validation`.

## Preconditions and required context selection
Run the context router. Read selected test notes and inspect the project's existing framework, test tasks, plugin versions, and available device/renderer.

## Applicable policy IDs
`testing_evidence`, `source_access`, `security`, `freshness`, `visual_baseline_approval`.

Consult the official `testing-setup` skill only when configuring test infrastructure; apply recommendations after compatibility and project-need review.

## Workflow
Separate unit, UI behavior, accessibility, screenshot and device checks. Verify tool/plugin compatibility before adding dependencies. For visual tests, keep approved references immutable and require a deliberate change to fail comparison.

## Verification
Report exact executed commands and results, test counts, renderer/device limits, and reference provenance. Exercise a deliberate regression when validating a new screenshot comparison mechanism.

## Failure and uncertainty
Do not equate successful compilation with UI behavior or visual quality. Mark unavailable emulator/device/screenshot evidence BLOCKED or NOT VERIFIED. Do not assume upstream default dependencies fit the project or claim inaccessible Figma content was reviewed.
