#!/usr/bin/env python3
"""Validate a saved route manifest against the published JSON Schema."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 scripts/validate_context_manifest.py MANIFEST.json", file=sys.stderr)
        return 2
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("BLOCKED: install development dependency from requirements-dev.txt", file=sys.stderr)
        return 2
    try:
        manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "routing/context-manifest.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda e: list(map(str, e.path)))
        if errors:
            for error in errors:
                print(f"FAIL: {list(error.path)}: {error.message}", file=sys.stderr)
            return 1
        print("PASS: context manifest conforms to routing/context-manifest.schema.json (Draft 2020-12).")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
