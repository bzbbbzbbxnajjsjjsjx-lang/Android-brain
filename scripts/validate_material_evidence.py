#!/usr/bin/env python3
"""Validate Material 3 URL discovery, retrieval, and verification evidence separately."""
from __future__ import annotations
import hashlib,json,re,sys
from datetime import date,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate_records(data:dict,topics:list,urls:list)->dict:
    topic_by_id={t["id"]:t for t in topics};url_set=set(urls);seen=set()
    if data.get("schema_version")!=1:raise ValueError("unsupported Material retrieval-evidence schema")
    for r in data.get("records",[]):
        if r.get("topic_id") not in topic_by_id:raise ValueError(f"unknown Material topic {r.get('topic_id')}")
        if r.get("canonical_url") not in url_set or r["canonical_url"] not in topic_by_id[r["topic_id"]]["canonical_source_urls"]:raise ValueError("retrieval evidence URL is not registered under its topic")
        if r["canonical_url"] in seen:raise ValueError("duplicate page evidence record")
        seen.add(r["canonical_url"])
        if not re.fullmatch(r"[a-f0-9]{64}",r.get("response_sha256","")):raise ValueError("invalid retrieval response hash")
        datetime.fromisoformat(r["retrieved_at"].replace("Z","+00:00"))
        state=r.get("state")
        if state=="verified":
            required=("page_content_obtained","verified","content_summary","reviewed_at","reviewer","source_section","content_sha256","content_character_count","content_retrieval_method")
            if not all(r.get(x) for x in required):raise ValueError("VERIFIED requires retrieved page content, summary, review date, reviewer, and source section")
            if not re.fullmatch(r"[a-f0-9]{64}",r["content_sha256"]) or not isinstance(r["content_character_count"],int) or r["content_character_count"]<200:raise ValueError("VERIFIED requires a content digest and a substantive page-content character count")
            if r.get("http_status")!=200 or not r.get("page_content_obtained") or not r.get("verified"):raise ValueError("VERIFIED contradicts retrieval evidence")
        elif state=="content_retrieved":
            if r.get("http_status")!=200 or not r.get("page_content_obtained") or r.get("verified"):raise ValueError("CONTENT_RETRIEVED must have page content but must not claim human verification")
            if not re.fullmatch(r"[a-f0-9]{64}",r.get("content_sha256","")) or not isinstance(r.get("content_character_count"),int) or r["content_character_count"]<200 or not r.get("content_retrieval_method"):raise ValueError("CONTENT_RETRIEVED requires a content digest, substantive text count, and retrieval method; shell metadata is insufficient")
        elif state=="retrieved_shell":
            if r.get("http_status")!=200 or r.get("page_content_obtained") or r.get("verified"):raise ValueError("retrieved shell cannot be reported as page content or verified")
        elif state=="discovered":
            if any(r.get(x) for x in ("http_status","response_sha256","page_content_obtained","verified")):raise ValueError("discovery-only record cannot claim retrieval evidence")
        else:raise ValueError(f"unsupported Material evidence state: {state}")
    for attempt in data.get("browser_attempts",[]):
        if attempt.get("canonical_url") not in url_set:raise ValueError("browser attempt URL is not in the official sitemap evidence")
        if not attempt.get("access_method") or not attempt.get("tls_verification"):raise ValueError("browser attempt must identify its method and TLS verification state")
        if attempt.get("page_content_obtained") or attempt.get("verified"):raise ValueError("failed browser retrieval cannot claim content or verification")
        if attempt.get("attempted_on") and date.fromisoformat(attempt["attempted_on"])>date.today():raise ValueError("browser attempt date cannot be in the future")
        if attempt.get("result")=="blocked_tls_validation" and (attempt.get("http_status") is not None or not attempt.get("error_code")):raise ValueError("TLS failure evidence cannot claim HTTP retrieval and must include its observed error code")
    record_counts={s:sum(1 for r in data.get("records",[]) if r["state"]==s) for s in ("discovered","retrieved_shell","content_retrieved","verified")}
    return {"topic_groups_discovered":len(topics),"discovered_urls":len(url_set),"page_evidence_record_counts":record_counts,"verified_page_content_topics":len({r["topic_id"] for r in data.get("records",[]) if r["state"]=="verified"})}
def main()->int:
    try:
        topics=json.loads((ROOT/"routing/material3-topics.json").read_text())["topics"]
        sitemap=json.loads((ROOT/"routing/material3-sitemap-evidence.json").read_text())["urls"]
        data=json.loads((ROOT/"routing/material3-retrieval-evidence.json").read_text())
        result=validate_records(data,topics,sitemap)
        print(f"PASS: {result['topic_groups_discovered']} topic groups and {result['discovered_urls']} URLs discovered; sampled page evidence={result['page_evidence_record_counts']}; verified page-content topics={result['verified_page_content_topics']}.")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:print(f"FAIL: {e}",file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
