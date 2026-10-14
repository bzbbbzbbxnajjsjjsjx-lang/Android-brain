# Harness architecture and P0-P3 assessment

## Repository and environment

The checkout began empty/unborn before P0/P1 work. Files from the earlier application scope in this same session were removed when the task was corrected to harness-only. This repository has no Android application, Gradle project, APK/AAB workflow, or Android runtime dependency.

Environment evidence: Linux x86_64; Java 21.0.12.1; Codex CLI 0.159.2. Android SDK/CLI are under shared `/workspace/tooling`; a selected official skill install was previously verified using a writable Android user home. ADB's default home was not writable and `/dev/kvm` was unavailable, so device execution remains blocked. P2 needs only Python 3 standard library and local JSON/Markdown.

## Data flow

`User task → deterministic keyword classification → taxonomy route → bounded source selection → knowledge/skill/policy manifest → freshness and validation contract`.

Native Codex mechanisms: repository `AGENTS.md` and `.agents/skills/<name>/SKILL.md`. Custom harness mechanisms: JSON source/skill/policy registries, `routing/task-taxonomy.json`, Material topic manifest, and `scripts/route_context.py`. JSON is not automatically loaded by Codex. The custom router recommends skill IDs but does not activate native skills, fetch external URLs, or claim selected files were read. No LLM, vector service, or orchestration runtime exists.

## P2 decisions

- Match normalized configured terms deterministically; preserve compact technical identifiers. Unknown tasks receive only global policy context; broad requests can be marked ambiguous.
- Taxonomy rules define an explicit eligible source set. Registry authority, version sensitivity, access status, limitations, and last verification are included in the decision manifest. Generic shared tags do not expand selection to every Android source.
- Global security, provenance, scope, source-access, reporting, test-evidence, freshness, and anti-hallucination policies cannot be removed by a task rule.
- Material.io design sources stay distinct from AndroidX APIs. Sitemap-listed topics establish a broad domain map, not article-content retrieval. Missing/unverified references are returned as limitations.
- Context is budgeted in characters using complete concise knowledge notes and policy summaries; skill instruction size is reported separately because router output cannot activate skills. No arbitrary truncation occurs.
- Every evaluation freezes `--as-of` to make freshness output reproducible.

## P3 skill handoff

The taxonomy recommends a small task-specific set of skills. `material3-expressive` is the single entrypoint for all 21 Material design topics; `kotlin-compose` covers UI implementation; `compose-architecture` covers architecture/Hilt/modules/variants; testing, visual validation, performance, and harness work remain separate domains. The overlapping `material-shapes-motion` skill was consolidated into the complete Material skill, and old references were migrated.

The router does not activate skills. Manifest evidence distinguishes files present, recommendations, native discovery/invocation observations, session reads, and live source checks. Codex CLI `debug prompt-input` exposed the Material skill activation description, so prompt-level metadata discovery is PASS. No LLM session trace exposed invocation or SKILL.md consumption; those remain NOT VERIFIED. The direct OpenAI Codex skill documentation could not be re-fetched under the managed environment's restricted network policy.

P3 tests remain Python-side only; no Android project, Gradle task, APK, or Compose UI is introduced.

See [routing contract](CONTEXT_ROUTER.md), [source audit](SOURCE_AUDIT.md), and [quality gates](QUALITY_GATES.md).

## P4 policy and evidence gate

The router manifest now feeds `scripts/evaluate_quality_gate.py` with a separately schema-validated evidence record. The evaluator checks exact policy applicability, manifest digest, registered source/skill/policy IDs, local knowledge paths, observed check consistency, source freshness, and harness-only artifact boundaries. Policy rule identifiers are allowlisted in Python; registry description strings are never interpreted as code. A result schema produces `PASS`, `FAIL`, `BLOCKED`, or `NOT VERIFIED`, and only `PASS` approves completion. Manual review and advisory guidance remain explicit non-automated states.

Evidence distinguishes reported assertions from observed tool output/artifacts/human reviews. Artifact hashes check content integrity but do not authenticate authorship. The local workspace scan detects known Android project/build artifacts and credential-like filenames; it is not a secret scanner. Hosted CI requires an observed provider run for merge/release completion and is not inferred from workflow configuration.

The existing repository has no tracked Git baseline: branch `work` has no commits and `git ls-files` is empty. Before P4 changes, a 73-file inventory and SHA-256 manifest were written to `/tmp/android-harness-p4-before.inventory` and `/tmp/android-harness-p4-before.sha256`; this preserves a comparison point without deleting or committing the untracked P0–P3 harness files. This repository integrity limitation is separate from policy evaluator behavior.
