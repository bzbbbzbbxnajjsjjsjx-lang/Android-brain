# Android Context Engineering Harness

A task-scoped Codex context foundation for Android engineering. It contains source-grounded knowledge notes, selected Google Android skills, machine-readable registries, a deterministic context router, and harness evaluations. It does not contain an Android application, Gradle project, or custom agent runtime.

## Route a future task

Run:

```bash
python3 scripts/route_context.py "<Android engineering task>" --as-of YYYY-MM-DD
```

Review the JSON recommendations, validate saved manifests with `python3 scripts/validate_context_manifest.py`, read only selected notes/skills, and perform requested live API/source checks. The router does not fetch sources or activate skills. See [routing contract](docs/CONTEXT_ROUTER.md), [Codex skill handoff](docs/CODEX_SKILL_INTEGRATION.md), [architecture](docs/ARCHITECTURE.md), [source audit](docs/SOURCE_AUDIT.md), and [knowledge index](knowledge/README.md).

## Validate the harness

```bash
python3 scripts/validate_registry.py
python3 scripts/validate_skills.py
python3 evals/run_context_router_evals.py
python3 evals/run_skill_integration_evals.py
```

`routing/task-taxonomy.json` contains deterministic routing rules; `routing/context-manifest.schema.json` documents the machine-readable output. `routing/material3-topics.json` records broad Material.io coverage, while `routing/material3-sitemap-evidence.json` preserves the official sitemap URLs used to establish those paths. Sitemap discovery is not a claim that each page's content was retrieved.

See the [first verified real Android engineering run](docs/REAL_ANDROID_VALIDATION.md) for a pinned Now in Android accessibility test executed on an API 34 GitHub Actions emulator, including evidence and limitations.
