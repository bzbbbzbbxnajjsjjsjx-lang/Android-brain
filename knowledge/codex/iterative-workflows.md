# Iterative Codex engineering

Treat agent work as a feedback loop: provide repository/task context, make a bounded change, run checks, inspect their actual output, and adjust. Front-load acceptance criteria and relevant context; use small, reviewable increments and preserve verification evidence. Repository instructions should state stable project-wide rules; specialized references and skills should be loaded only for relevant work.

This harness operationalizes that advice through `AGENTS.md`, task-scoped `.agents/skills/`, the source registry, and a registry validator. Codex natively discovers repository instructions and supported skills; it does not automatically load arbitrary registry JSON or route tasks from it. No agent runtime or memory service is needed.

**Provenance:** `codex_workflows`, especially the cookbook workflow discussion on iterative development and context. The cookbook is an example, not a normative Codex protocol.
