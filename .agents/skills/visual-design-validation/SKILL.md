---
name: visual-design-validation
description: Compare rendered Android UI with an approved visual reference or review a design handoff for measurable differences.
---

## Scope
Rendered visual evidence, reference provenance, screenshot comparisons and approval status. Figma is optional.

## Preconditions and required context selection
Run the context router and read selected visual/screenshot notes. Require an approved target reference or explicit design specification, plus an actual rendered output to compare.

## Applicable policy IDs
`visual_baseline_approval`, `accessibility_review`, `source_access`, `provenance`, `testing_evidence`.

Read `knowledge/integrations/figma-workflow.md` only when a Figma handoff is part of the task.

## Workflow
Record reference and render paths, provenance, target size/theme/font scale/state, comparison method, and reviewer approval. Inspect layout, wrapping, hierarchy, color, density, themes and relevant states. Keep approved references separate from candidates.

## Verification
Report measurable diffs and actual inspected images. Require explicit review before replacing approved baselines; test that a deliberate visual change fails comparison when setting up regression detection.

## Failure and uncertainty
Figma pages were blocked in this environment; no layers, assets or tokens may be inferred. A build or screenshot file existing does not prove it was inspected. Report missing references/rendering and comparison limitations as BLOCKED or NOT VERIFIED.
