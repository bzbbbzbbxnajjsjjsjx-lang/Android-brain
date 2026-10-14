# Engineering policy evaluation

`registry/policies.json` is the stable policy registry and carries P4 applicability, enforcement mode, evidence requirements, fixed rule ID, severity, remediation, exceptions, and source provenance. `scripts/evaluate_quality_gate.py` implements an allowlist of rule IDs in ordinary Python; registry procedure strings are descriptive and are never executed.

Enforcement modes have distinct meanings:

- `deterministic_automated`: locally checkable structure, identifiers, artifact scope, or evidence consistency.
- `runtime_tool_dependent`: requires observed current source, project dependency, test, or benchmark tool output; unavailable infrastructure is `BLOCKED`, absent evidence is `NOT VERIFIED`.
- `manual_review`: requires observed reviewer/outcome evidence; otherwise `NOT VERIFIED`.
- `advisory_guidance`: emitted as `ADVISORY`, never presented as mechanical compliance.

The evaluator consumes `policies/evidence.schema.json` and the router manifest. It checks the manifest digest, policy/source/skill IDs, local knowledge paths, evidence links, actual exit code, artifact digest when a local artifact is supplied, and a read-only workspace scan. The scan detects common Android project/build artifacts and credential-like filenames; it is not a secret scanner or an authenticity system. Hashes detect content mismatch, not who produced the evidence.

Use:

```bash
python3 scripts/route_context.py "<task>" --as-of YYYY-MM-DD > /tmp/context-manifest.json
python3 scripts/evaluate_quality_gate.py --manifest /tmp/context-manifest.json --evidence /path/to/evidence.json
```

Exit codes are `0 PASS`, `1 FAIL`, `2 BLOCKED`, and `3 NOT VERIFIED`. A complete task requires `PASS`; any `FAIL`, `BLOCKED`, or `NOT VERIFIED` prevents approval. Hosted CI is required for merge/release completion scopes and remains unverified without an observed run URL/result. Local checks cannot prove hosted CI.
