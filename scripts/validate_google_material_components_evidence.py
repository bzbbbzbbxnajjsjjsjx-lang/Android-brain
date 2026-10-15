#!/usr/bin/env python3
"""Validate pinned Google Material Components View-doc evidence separately from Material.io/Compose."""
from __future__ import annotations
import json,re,sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
SHA=re.compile(r"^[a-f0-9]{64}$")
REV=re.compile(r"^[a-f0-9]{40}$")
REPO="https://github.com/material-components/material-components-android"
VIEW_TYPES={"view_component_guide","repository_maintenance_notice"}

def validate(data:dict,registry:dict,topics:list)->dict:
    if data.get("schema_version")!=1 or data.get("source_family")!="official_google_material_components_android_view_docs":
        raise ValueError("unsupported Material Components evidence schema/family")
    if data.get("repository")!=REPO or not REV.fullmatch(data.get("repository_revision","")):
        raise ValueError("repository/revision provenance is invalid")
    rev=data["repository_revision"]
    sources={x["id"]:x for x in registry["sources"]}; seen=set()
    for row in data.get("records",[]):
        # Registry and evidence use the same stable `id` field, as the P8
        # Google Android evidence records do. Do not silently accept aliases.
        sid=row.get("id")
        if sid in seen:raise ValueError(f"duplicate source record: {sid}")
        seen.add(sid)
        src=sources.get(sid)
        if not src or src.get("owner")!="Google / Material Components for Android" or src.get("source_type") not in VIEW_TYPES or src.get("authority_level")!="official_legacy_view_implementation":
            raise ValueError(f"unregistered or misclassified official View source: {sid}")
        url=row.get("canonical_url","")
        if url!=src["canonical_url"] or urlparse(url).hostname!="github.com" or f"/{rev}/" not in url:
            raise ValueError(f"source URL/revision mismatch: {sid}")
        if row.get("repository_revision")!=rev or row.get("source_family")!="google_material_components_view_documentation":
            raise ValueError(f"source-family/revision mismatch: {sid}")
        states={"discovery_state":"DISCOVERED","retrieval_state":"RETRIEVED","verification_state":"VERIFIED","integration_state":"INTEGRATED"}
        if any(row.get(k)!=v for k,v in states.items()):raise ValueError(f"incomplete or overstated source state chain: {sid}")
        if row.get("http_status")!=200 or "TLS verification enabled" not in row.get("access_method","") or "raw.githubusercontent.com" not in row.get("access_method",""):
            raise ValueError(f"unsupported or incomplete retrieval evidence: {sid}")
        if not SHA.fullmatch(row.get("sha256","")) or row.get("sha256")!=row.get("content_sha256"):
            raise ValueError(f"invalid body digest: {sid}")
        if not isinstance(row.get("bytes"),int) or row["bytes"]<1000 or not isinstance(row.get("characters"),int) or row["characters"]<1000:
            raise ValueError(f"insufficient retrieved Markdown body evidence: {sid}")
        if not row.get("sections") or not row.get("local_knowledge_reference") or row.get("content_mime_type") != "text/markdown":
            raise ValueError(f"missing inspected sections or integrated note: {sid}")
        if date.fromisoformat(src["last_verified"])>date.today():raise ValueError(f"future registry verification date: {sid}")
        ref=(ROOT/row["local_knowledge_reference"]).resolve()
        if not ref.is_relative_to(ROOT) or not ref.is_file():
            raise ValueError(f"missing or unattributed local note: {sid}")
        note_text=ref.read_text(encoding="utf-8")
        note=note_text.lower()
        if sid not in note_text or url not in note_text or row["sha256"] not in note_text or rev not in note_text:
            raise ValueError(f"local note provenance does not match source evidence: {sid}")
        if "view/xml" not in note or "not a jetpack compose" not in note:
            raise ValueError(f"View/Compose boundary missing from note: {sid}")
    license=data.get("upstream_license_evidence",{})
    if license.get("license")!="Apache-2.0" or license.get("http_status")!=200 or f"/{rev}/LICENSE" not in license.get("canonical_url","") or not SHA.fullmatch(license.get("response_sha256","")):
        raise ValueError("upstream Apache-2.0 license evidence is missing or invalid")
    # None of these legacy GitHub records may become Material.io page evidence or a Compose API.
    if any(srcid in {s["id"] for s in sources.values() if s["source_type"]=="api_reference"} for srcid in seen):
        raise ValueError("View documentation has been misclassified as an AndroidX API source")
    topic_ids={sid for t in topics for sid in t.get("legacy_view_context",{}).get("source_ids",[])}
    topic_refs={p for t in topics for p in t.get("legacy_view_context",{}).get("knowledge_references",[])}
    if not seen<=topic_ids or not {x["local_knowledge_reference"] for x in (sources[s] for s in seen)}<=topic_refs:
        raise ValueError("verified View source is not connected to the Material topic manifest")
    return {"verified_view_documents":len(seen),"integrated_view_documents":sum(x.get("integration_state")=="INTEGRATED" for x in data["records"]),"repository_revision":rev}

def main()->int:
    try:
        data=json.loads((ROOT/"routing/material-components-android-evidence.json").read_text())
        reg=json.loads((ROOT/"registry/sources.json").read_text())
        topics=json.loads((ROOT/"routing/material3-topics.json").read_text())["topics"]
        result=validate(data,reg,topics)
        print(f"PASS: {result['verified_view_documents']} official Google View/XML Markdown documents verified and routed at {result['repository_revision']}; no Compose API or Material.io page claims.")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}",file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
