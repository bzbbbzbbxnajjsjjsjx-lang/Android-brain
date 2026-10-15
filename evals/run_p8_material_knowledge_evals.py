#!/usr/bin/env python3
"""P8 evidence and routing checks for official Google Material/Compose knowledge."""
from __future__ import annotations
import copy, json, sys
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import route_context as router
import validate_google_android_evidence as google
import validate_material_evidence as material

def main()->int:
    checks=[]
    def check(name, ok, detail):
        checks.append((name,bool(ok),detail))
        if not ok: raise AssertionError(f"{name}: {detail}")
    registry=json.loads((ROOT/"registry/sources.json").read_text())
    evidence=json.loads((ROOT/"routing/google-android-retrieval-evidence.json").read_text())
    result=google.validate(evidence,registry)
    check("official_google_allowlist_and_provenance",result["records"]==5,"Only registered HTTPS developer.android.com records with body hashes and section evidence are accepted.")
    check("explicit_knowledge_state_chain",all(all(x.get(k)==v for k,v in (("discovery_state","DISCOVERED"),("retrieval_state","RETRIEVED"),("verification_state","VERIFIED"),("integration_state","INTEGRATED"))) for x in evidence["records"]),"Discovery, body retrieval, content review, and router knowledge integration are separate recorded states.")
    bad=copy.deepcopy(evidence);bad["records"][0]["canonical_url"]="https://material-docs.example/compose"
    try:google.validate(bad,registry); rejected=False
    except ValueError:rejected=True
    check("third_party_provider_rejected",rejected,"Non-Google documentation hosts are rejected.")
    shell=copy.deepcopy(evidence);shell["records"][0]["content_extraction"]="JavaScript shell"
    try:google.validate(shell,registry); rejected=False
    except ValueError:rejected=True
    check("shell_is_not_content",rejected,"A shell cannot satisfy retrieved or verified article evidence.")
    overstated=copy.deepcopy(evidence);overstated["records"][0]["verification_state"]="NOT VERIFIED"
    try:google.validate(overstated,registry); rejected=False
    except ValueError:rejected=True
    check("state_transition_integrity",rejected,"A retrieved but unverified page cannot be reported as integrated verified knowledge.")
    bad=copy.deepcopy(evidence);bad["records"][0]["response_sha256"]="0"*63
    try:google.validate(bad,registry); rejected=False
    except ValueError:rejected=True
    check("digest_integrity_shape",rejected,"Malformed evidence digests fail validation; digests are not presented as signatures.")
    topics=json.loads((ROOT/"routing/material3-topics.json").read_text())["topics"]
    sitemap=json.loads((ROOT/"routing/material3-sitemap-evidence.json").read_text())["urls"]
    m3=json.loads((ROOT/"routing/material3-retrieval-evidence.json").read_text())
    counts=material.validate_records(m3,topics,sitemap)
    site=next(x for x in registry["sources"] if x["id"]=="material3_site")
    check("source_family_separation",site["accessibility_status"]=="partial_js_shell" and counts["verified_page_content_topics"]==0 and len(topics)==21 and len(sitemap)==249,"Material.io remains shell-only at 0/21 verified; all 21 groups and 249 URLs remain; Android Developers evidence is separate.")
    unverified_notes=[(ROOT/"knowledge/material3"/f).read_text(encoding="utf-8").lower() for f in ("principles.md","motion.md","shapes.md")]
    check("unverified_material_guidance_not_fabricated",all(("not retrieved" in x or "not verified" in x) and ("no page-specific" in x or "no material-specific" in x) for x in unverified_notes),"Material.io shell-only topics remain access notes and do not present invented page-specific rules as verified knowledge.")
    manifest=router.build_manifest("Implement a Material 3 color system in Jetpack Compose.")
    refs={x["path"] for x in manifest["selected_knowledge_references"]}
    ids={x["id"] for x in manifest["selected_sources"]}
    check("verified_knowledge_router_integration","knowledge/androidx/compose-material3-system.md" in refs and "androidx_compose_material3_guide" in ids,"Relevant Material 3 implementation task selects the verified Android Developers note and source.")
    check("design_content_limitation_preserved",any(x.get("kind")=="material_page_content_unverified" for x in manifest["missing_or_inaccessible_context"]),"Router keeps Material.io design-content retrieval limitation visible.")
    check("target_api_compatibility_not_assumed",any(x.get("kind")=="live_verification_not_performed" and x.get("source_id")=="androidx_compose_material3_guide" for x in manifest["missing_or_inaccessible_context"]) and any("target dependency" in x.lower() or "target project androidx dependency" in x.lower() for x in manifest["required_verification_actions"]),"The router still requires a target-project dependency/API check.")
    manifest2=router.build_manifest("Implement a Material 3 color system in Jetpack Compose.")
    check("deterministic_manifest",json.dumps(manifest,sort_keys=True)==json.dumps(manifest2,sort_keys=True),"Identical task and registry state produce identical logical JSON.")
    unknown=copy.deepcopy(registry);next(x for x in unknown["sources"] if x["id"]=="androidx_compose_material3_guide")["canonical_url"]="https://third-party.example/doc"
    try:google.validate(evidence,unknown); rejected=False
    except ValueError:rejected=True
    check("registry_canonical_url_tamper_detected",rejected,"Evidence must match its canonical registry URL.")
    print(f"P8 material knowledge evaluations {sum(ok for _,ok,_ in checks)}/{len(checks)} PASS")
    for name,ok,detail in checks:print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (AssertionError,KeyError,OSError,ValueError,json.JSONDecodeError) as exc:print(f"FAIL: {exc}",file=sys.stderr);raise SystemExit(1)
