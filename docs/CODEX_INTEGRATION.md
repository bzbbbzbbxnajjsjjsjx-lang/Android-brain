# Codex execution and evidence contract

Codex-native `AGENTS.md` instructions and `.agents/skills/*/SKILL.md` discovery remain the supported instruction mechanisms. The deterministic router is a local Python selector and returns recommendations; its JSON registry is custom harness metadata, not a native Codex feature and not a skill activator.

For a task, run `python3 scripts/route_context.py "<task>" --as-of YYYY-MM-DD`, validate its manifest, inspect selected policy IDs and unavailable/stale source records, then read the selected skill and knowledge files required by the task. Codex instructions may guide skill use, but the router cannot show whether Codex invoked or consumed a skill. Record only observable evidence for discovery, invocation, `SKILL.md` reads, knowledge reads, and live source checks.

After execution, record evidence according to `policies/evidence.schema.json` and run `scripts/evaluate_quality_gate.py`. The evaluator verifies the supplied manifest digest, registry identifiers, local paths, evidence consistency, applicable fixed rules, and workspace artifact scope. It does not prove author identity. For merge/release scope, a real hosted CI run URL/result is required; a workflow definition or local check is insufficient.
