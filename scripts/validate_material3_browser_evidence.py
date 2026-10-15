#!/usr/bin/env python3
"""Validate Material.io browser acquisition evidence without making network calls."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import material3_knowledge_pipeline as pipeline

def main() -> int:
    try:
        topics, sitemap = pipeline.load_registry(ROOT)
        data = pipeline.load_evidence(ROOT / "routing/material3-browser-retrieval-evidence.json")
        try:
            import jsonschema
            schema = json.loads((ROOT / "routing/material3-browser-retrieval-evidence.schema.json").read_text())
            jsonschema.validate(data, schema)
        except ImportError:
            pass
        counts = pipeline.validate_evidence(data, topics, sitemap, root=ROOT)
        print(f"PASS: Material.io browser evidence validated; {len(topics['topics'])} topics, {len(sitemap['urls'])} URLs; page states={counts}; no network request made.")
        return 0
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
if __name__ == "__main__": raise SystemExit(main())
