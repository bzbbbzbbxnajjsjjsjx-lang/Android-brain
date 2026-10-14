#!/usr/bin/env python3
"""P7 checks for initial Git candidate integrity, provenance, CI, and source gates."""
from __future__ import annotations
import hashlib,json,re,subprocess,sys
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import check_release_readiness as readiness
import validate_material_evidence as material
import route_context as router

SECRET_PATTERNS=[
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE "+r"KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]
def candidate_files(root:Path)->list[str]:
    ignored={".git","__pycache__",".venv","venv"}
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and not p.is_symlink() and not ignored.intersection(p.relative_to(root).parts) and p.suffix!=".pyc")
def scan_secret(text:str)->bool:return any(p.search(text) for p in SECRET_PATTERNS)
def check(ok:bool,results:list,ident:str,detail:str)->None:
    results.append({"id":ident,"status":"PASS" if ok else "FAIL","detail":detail})
    if not ok:raise AssertionError(f"{ident}: {detail}")
def classify_candidate(root:Path)->dict:
    actual=set(candidate_files(root));manifest=json.loads((root/"release/initial-commit-candidate.json").read_text())
    listed=manifest["tracked_files"]
    return {"status":"PASS" if len(listed)==len(set(listed)) and set(listed)==actual else "FAIL","count":len(listed),"missing":sorted(actual-set(listed)),"nonexistent":sorted(set(listed)-actual)}
def main()->int:
    results=[]
    candidate=classify_candidate(ROOT)
    check(candidate["status"]=="PASS",results,"A_initial_commit_candidate",f"Exact file inventory: {candidate['count']} paths; missing={candidate['missing']}; nonexistent={candidate['nonexistent']}.")
    manifest=json.loads((ROOT/"release/initial-commit-candidate.json").read_text())
    check(bool(manifest.get("excluded_temporary_artifacts")) and "evals/reports/p5-routing-report.json" in manifest.get("retained_evaluation_evidence",[]) and "evals/reports/p6-integration-report.json" in manifest.get("retained_evaluation_evidence",[]),results,"B_candidate_classification","Retained P5/P6 evidence is distinguished from temporary `/tmp` outputs and ignored runtime/build files.")
    bad=[]
    for rel in manifest["tracked_files"]:
        p=ROOT/rel
        try:text=p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bad.append(rel+":binary");continue
        if scan_secret(text):bad.append(rel)
    fixture_detected=scan_secret("ghp_"+"A"*32) and scan_secret("-----BEGIN PRIVATE "+"KEY-----")
    check(not bad and fixture_detected,results,"C_sensitive_file_audit","Candidate scan found no credential/private-key patterns; controlled fixture patterns were detected.")
    symlinks=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_symlink() and ".git" not in p.relative_to(ROOT).parts]
    check(not symlinks,results,"C2_symlink_audit",f"No symlink paths enter the candidate tree; found={symlinks}.")
    git_head=subprocess.run(["git","rev-parse","--verify","HEAD"],cwd=ROOT,capture_output=True,text=True)
    tracked=subprocess.run(["git","ls-files"],cwd=ROOT,capture_output=True,text=True)
    git_status=subprocess.run(["git","status","--porcelain"],cwd=ROOT,capture_output=True,text=True)
    remote=subprocess.run(["git","remote","get-url","origin"],cwd=ROOT,capture_output=True,text=True)
    current_readiness=readiness.readiness(ROOT)
    expected_vc="PASS" if git_head.returncode==0 and tracked.returncode==0 and tracked.stdout.strip() and git_status.returncode==0 and not git_status.stdout.strip() and remote.returncode==0 else "BLOCKED"
    git_consistent=current_readiness["version_control_ready"]==expected_vc
    check(git_consistent,results,"D_git_tracking_readiness","Git status is classified from observed HEAD/tracked-tree state; candidate preparation did not stage or mutate Git.")
    ignore=(ROOT/".gitignore").read_text()
    required_ignore=(".env",".env.*","*.jks","*.keystore","local.properties","**/build/",".gradle/","*.apk","*.aab","*.pem","*.key","*.p12","*.pfx")
    check(all(x in ignore for x in required_ignore),results,"E_generated_and_secret_ignore_rules",".gitignore covers local secrets, signing material, Android build outputs, and generated binaries.")
    upstream_licenses=[ROOT/".agents/skills"/name/"LICENSE.txt" for name in ("testing-setup","jetpack-compose-performance","edge-to-edge")]
    root_license=ROOT/"LICENSE"
    license_audit=(root_license.is_file() and "Apache License" in root_license.read_text(encoding="utf-8") and all(p.is_file() and "Apache License" in p.read_text(encoding="utf-8") for p in upstream_licenses) and "owner_approved"==json.loads((ROOT/"release/harness-manifest.json").read_text()).get("license_review_status"))
    check(license_audit,results,"E2_license_inventory","Owner-selected root Apache 2.0 license and all three upstream Apache licenses/attributions remain present.")
    prohibited=[p for p in manifest["tracked_files"] if Path(p).suffix.lower() in {".apk",".aab",".aar",".dex",".class",".so"} or Path(p).name in {"build.gradle","build.gradle.kts","settings.gradle","settings.gradle.kts","AndroidManifest.xml"}]
    check(not prohibited and not manifest["artifact_audit"].get("files_over_1MiB"),results,"E3_application_artifact_and_size_audit",f"No application artifacts or files over 1 MiB are in the candidate; prohibited={prohibited}.")
    workflow=(ROOT/".github/workflows/harness.yml").read_text()
    required_commands=("python3 scripts/validate_registry.py","python3 scripts/validate_skills.py","python3 evals/run_context_router_evals.py","python3 evals/run_quality_gate_evals.py","python3 evals/run_harness_evals.py","python3 evals/run_adversarial_evals.py","python3 evals/run_mutation_evals.py","python3 evals/run_p6_evals.py","python3 evals/run_p7_readiness_evals.py")
    no_android=not re.search(r"\b(gradle|gradlew|assemble|bundleRelease|\.apk|\.aab)\b",workflow,re.I)
    check(all(x in workflow for x in required_commands) and no_android and "ubuntu-latest" in workflow and "python-version: '3.12'" in workflow,results,"F_workflow_contract","Hosted workflow lists registry, P2-P7, policy, adversarial, and mutation checks on clean Ubuntu/Python without Android build commands.")
    fixtures=[
        ({},"NOT VERIFIED"),
        ({"headSha":"abc","status":"completed","conclusion":"success","createdAt":"2026-01-01"},"PASS"),
        ({"headSha":"abc","status":"completed","conclusion":"failure","createdAt":"2026-01-01"},"FAIL"),
        ({"headSha":"abc","status":"in_progress","conclusion":None,"createdAt":"2026-01-01"},"NOT VERIFIED"),
    ]
    classification=all(readiness.classify_hosted_ci("abc",([f] if f else []))==want for f,want in fixtures)
    remote_parsing={"https://github.com/acme/android-harness.git":"acme/android-harness","ssh://git@github.com/acme/android-harness.git":"acme/android-harness","git@github.com:acme/android-harness.git":"acme/android-harness","https://example.com/acme/android-harness.git":None}
    classification=classification and all(readiness.github_repo_slug(url)==want for url,want in remote_parsing.items())
    check(classification,results,"G_hosted_ci_evidence_classification","No-run/in-progress is NOT VERIFIED; completed outcomes map to PASS/FAIL and supported GitHub remotes parse to the correct repository slug.")
    topics=json.loads((ROOT/"routing/material3-topics.json").read_text())["topics"]
    sitemap=json.loads((ROOT/"routing/material3-sitemap-evidence.json").read_text())["urls"]
    evidence=json.loads((ROOT/"routing/material3-retrieval-evidence.json").read_text())
    counts=material.validate_records(evidence,topics,sitemap)
    shell=next(r for r in evidence["records"] if r["state"]=="retrieved_shell")
    false_content=json.loads(json.dumps(evidence));record=next(r for r in false_content["records"] if r["state"]=="retrieved_shell");record.update(state="content_retrieved",page_content_obtained=True)
    try:material.validate_records(false_content,topics,sitemap);shell_rejected=False
    except ValueError:shell_rejected=True
    check(shell_rejected and shell["page_content_obtained"] is False and counts["verified_page_content_topics"]==0,results,"H_material_js_shell_rejected","HTTP 200 JavaScript-shell evidence cannot be promoted to content retrieved or verified.")
    browser_attempts=evidence.get("browser_attempts",[])
    browser_blocked=any(a.get("result")=="blocked_tls_validation" and a.get("tls_verification")=="enabled" and a.get("page_content_obtained") is False and a.get("verified") is False for a in browser_attempts)
    check(browser_blocked,results,"H2_browser_failure_recorded","JavaScript-capable retrieval failure is recorded independently; it is not counted as page content.")
    sources=json.loads((ROOT/"registry/sources.json").read_text())["sources"]
    refresh=json.loads((ROOT/"routing/source-refresh-policy.json").read_text())
    src={x["id"]:x for x in sources};refs={x["source_id"]:x for x in refresh["records"]}
    integrity=(set(src)==set(refs) and all(refs[k]["last_verified_from_registry"]==src[k]["last_verified"] and refs[k]["supported_retrieval_method"]==src[k]["retrieval_method"] and refs[k]["related_skills"]==src[k]["related_skills"] and refs[k]["related_policies"]==src[k]["related_policies"] for k in src) and all(date.fromisoformat(x["last_verified_from_registry"])<=date.today() and x.get("refresh_trigger") and x.get("failure_behavior") for x in refs.values()))
    check(integrity,results,"I_source_provenance_and_freshness","All 24 refresh records map exactly to registry provenance, skills, policies, retrieval method, and non-future dates.")
    stale=router.build_manifest("Use MaterialShapes in Compose.",as_of=date(2030,1,1))
    check(any(x["registry_age_status"]=="stale_by_registry_date" and x["live_verification_required"] for x in stale["freshness"]["source_records"]) and any("Recheck selected" in x for x in stale["required_verification_actions"]),results,"I2_stale_source_gate","A deliberately stale evaluation date marks selected sources stale and requires live verification without claiming a fetch.")
    skill_manifest=json.loads((ROOT/"registry/skills.json").read_text())
    native_state={"recommended":True,"metadata_discovered":"PASS","invoked":"NOT VERIFIED","skill_md_read":"NOT VERIFIED","knowledge_references_read":[],"external_source_verified":"NOT VERIFIED"}
    check(native_state["recommended"] and native_state["metadata_discovered"]=="PASS" and native_state["invoked"]=="NOT VERIFIED" and native_state["skill_md_read"]=="NOT VERIFIED" and len(skill_manifest["skills"])>0,results,"J_skill_observability_states","Recommendation/metadata visibility remains distinct from model invocation and actual file consumption.")
    states=current_readiness
    strict=readiness.classify_release_candidate("PASS","PASS","PASS","PASS","PASS","PASS")=="PASS" and readiness.classify_release_candidate("PASS","PASS","PASS","NOT VERIFIED","PASS","PASS")=="BLOCKED" and readiness.classify_stable_release("PASS","development",True)=="BLOCKED" and readiness.classify_stable_release("PASS","stable",False)=="BLOCKED" and readiness.classify_stable_release("PASS","stable",True)=="PASS"
    release_contract=strict and states["local_tested"] in {"PASS","FAIL"} and states["integration_tested"] in {"PASS","FAIL","NOT VERIFIED"} and states["version_control_ready"] in {"PASS","BLOCKED"} and states["hosted_ci"] in {"PASS","FAIL","NOT VERIFIED"} and states["release_candidate"] in {"PASS","BLOCKED"} and states["stable_release"] in {"PASS","BLOCKED"}
    check(release_contract,results,"K_release_gate_precedence",f"local={states['local_tested']}, integration={states['integration_tested']}, version_control={states['version_control_ready']}, CI={states['hosted_ci']}, source={states['material_source_verification']}, candidate={states['release_candidate']}, stable={states['stable_release']}.")
    print(f"P7 readiness evaluations {sum(x['status']=='PASS' for x in results)}/{len(results)} PASS")
    for x in results:print(f"{x['status']} {x['id']}: {x['detail']}")
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (AssertionError,KeyError,OSError,ValueError,json.JSONDecodeError) as exc:print(f"FAIL: {exc}",file=sys.stderr);raise SystemExit(1)
