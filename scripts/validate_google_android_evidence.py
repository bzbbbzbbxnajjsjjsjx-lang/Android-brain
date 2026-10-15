#!/usr/bin/env python3
"""Validate retrieved Android Developers knowledge without altering Material.io coverage."""
from __future__ import annotations
import hashlib, json, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_HOSTS = {"developer.android.com"}
HEX = re.compile(r"^[a-f0-9]{64}$")

def validate(data: dict, registry: dict) -> dict:
    if data.get("schema_version") != 1 or data.get("source_family") != "official_google_android_documentation":
        raise ValueError("unsupported Google Android retrieval evidence schema/family")
    sources = {x["id"]: x for x in registry["sources"]}
    seen = set()
    for row in data.get("records", []):
        sid = row.get("source_id")
        if sid in seen: raise ValueError(f"duplicate evidence source: {sid}")
        seen.add(sid)
        source = sources.get(sid)
        if not source: raise ValueError(f"unregistered source: {sid}")
        url = row.get("canonical_url", "")
        if url != source["canonical_url"]: raise ValueError(f"canonical URL mismatch: {sid}")
        if urlparse(url).scheme != "https" or urlparse(url).hostname not in OFFICIAL_HOSTS:
            raise ValueError(f"non-allowlisted documentation host: {url}")
        if source.get("owner") not in {"Android Developers / AndroidX", "Google Android"}:
            raise ValueError(f"non-Google source owner: {sid}")
        if row.get("source_family") not in {"official_androidx_api_reference", "official_android_developers_implementation"}:
            raise ValueError(f"invalid source family: {sid}")
        if row.get("http_status") != 200 or row.get("access_method", "").find("TLS verification") < 0:
            raise ValueError(f"retrieval evidence incomplete: {sid}")
        if row.get("content_extraction") in {"JavaScript shell", "HTML shell", "metadata only"}:
            raise ValueError(f"shell/metadata is not page content: {sid}")
        if not HEX.fullmatch(row.get("response_sha256", "")) or not HEX.fullmatch(row.get("content_sha256", "")):
            raise ValueError(f"invalid content digest: {sid}")
        if not isinstance(row.get("response_bytes"), int) or row["response_bytes"] < 1 or not isinstance(row.get("content_character_count"), int) or row["content_character_count"] < 200:
            raise ValueError(f"insufficient body evidence: {sid}")
        if not row.get("inspected_sections") or not all(isinstance(x, str) and x for x in row["inspected_sections"]):
            raise ValueError(f"no inspected sections recorded: {sid}")
        for field in ("retrieved_at", "verified_at"):
            observed = date.fromisoformat(row[field])
            if observed > date.today(): raise ValueError(f"future {field}: {sid}")
        expected_states={"discovery_state":"DISCOVERED","retrieval_state":"RETRIEVED","verification_state":"VERIFIED","integration_state":"INTEGRATED"}
        if any(row.get(field)!=state for field,state in expected_states.items()):
            raise ValueError(f"invalid or overstated knowledge state: {sid}")
        if row.get("integrated") is not True:
            raise ValueError(f"knowledge not integrated: {sid}")
        ref = row.get("local_knowledge_reference", "")
        path = (ROOT / ref).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file(): raise ValueError(f"missing/unsafe knowledge reference: {sid}")
        if sid not in path.read_text(encoding="utf-8"): raise ValueError(f"knowledge reference lacks provenance ID: {sid}")
    if not seen: raise ValueError("no official Android documentation records")
    return {"records": len(seen), "knowledge_integrated": sum(x.get("integrated") is True for x in data["records"]), "source_families": sorted({x["source_family"] for x in data["records"]})}

def main() -> int:
    try:
        data=json.loads((ROOT/"routing/google-android-retrieval-evidence.json").read_text())
        registry=json.loads((ROOT/"registry/sources.json").read_text())
        result=validate(data, registry)
        print(f"PASS: {result['records']} official Android Developers/API records; {result['knowledge_integrated']} integrated; families remain separated. Hashes are integrity identifiers, not signed authenticity proofs.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr); return 1

if __name__ == "__main__": raise SystemExit(main())
