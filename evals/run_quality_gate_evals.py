#!/usr/bin/env python3
"""P4 policy/evidence quality gate evaluations using in-memory test cases."""
from __future__ import annotations
import hashlib, importlib.util, json, sys, tempfile, subprocess
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("quality_gate", ROOT/"scripts/evaluate_quality_gate.py")
q=importlib.util.module_from_spec(spec); sys.modules[spec.name]=q; spec.loader.exec_module(q)
router_spec=importlib.util.spec_from_file_location("route_context", ROOT/"scripts/route_context.py")
r=importlib.util.module_from_spec(router_spec); sys.modules[router_spec.name]=r; router_spec.loader.exec_module(r)
AS_OF=__import__('datetime').date(2026,10,14)
def route(task): return r.build_manifest(task, as_of=AS_OF)
def digest(m): return "sha256:"+hashlib.sha256(q.canonical(m)).hexdigest()
def ev(m, taskid="eval-task", kind="android", claims=None, checks=None, **kwargs):
    return {"schema_version":1,"task":{"id":taskid,"kind":kind,"description":m["input_task"],"completion_scope":"local"},
      "context_manifest_digest":digest(m),"applicable_policy_ids":sorted(x["id"] for x in m["selected_policies"]),"claims":claims or [],"checks":checks or [],
      "skill_evidence":{"skill_id":(m.get("selected_skills", [{}])[0].get("id", "")),"registered":True,"recommended":True,"metadata_discovered":True,"invoked":False,"skill_md_read":False,"knowledge_references_read":[],"external_source_verified":False,"evidence_origin":"observed_tool_output"},
      "environment_limitations":[],**kwargs}
def check(cid,pid,status="PASS",code=0, origin="observed_tool_output", **kwargs):
    return {"id":cid,"policy_id":pid,"status":status,"command_or_tool":"python3 scripts/validate_registry.py","exit_code":code,
      "observed_at":datetime.now(timezone.utc).isoformat(),"artifact_ref":"validation-output.txt","artifact_sha256":"0"*64,
      "evidence_origin":origin,"environment_limitations":[],"verification_result":"captured process output","human_approval_required":False,"details":{},**kwargs}
def result(task, **kw):
    m=route(task); e=ev(m, **kw); out=q.evaluate(e,m,Path(kw["workspace_root"]) if kw.get("workspace_root") else ROOT)
    schema_errors=q.validate_schema(out,ROOT/"policies/quality-gate-result.schema.json")
    need(not schema_errors, f"quality gate result schema invalid: {schema_errors}")
    return out,e,m

def need(test, msg):
    if not test: raise AssertionError(msg)
def run():
    passed=[]
    # A: unsupported successful validation without observed output.
    x,_,_=result("Improve Android context routing.",kind="harness_only",checks=[{"id":"fake","policy_id":"testing_evidence","status":"PASS","evidence_origin":"reported_assertion","verification_result":"said so"}])
    need(x["overall_status"]=="NOT VERIFIED","A: assertion became PASS"); passed.append("A missing evidence")
    # B: deterministic workspace violation.
    with tempfile.TemporaryDirectory() as t:
        Path(t,"oops.apk").write_bytes(b"test artifact")
        x,_,_=result("Improve Android context routing.",kind="harness_only",workspace_root=t)
        need(any(p["policy_id"]=="scope_isolation" and p["status"]=="FAIL" for p in x["policy_results"]),"B artifact not rejected")
    passed.append("B prohibited artifact")
    # C: unverified experimental AndroidX API.
    x,_,_=result("Implement experimental MaterialShapes API in Compose.",claims=[{"type":"experimental_api","value":"new api","source_ids":["material_shapes_api"],"details":{"api_name":"unverified"}}])
    need(x["overall_status"]=="NOT VERIFIED","C experimental API not held"); passed.append("C experimental API")
    # D: inaccessible Figma claim lacks exported artifact.
    x,_,_=result("Extract design tokens from the Material 3 Figma Design Kit.",claims=[{"type":"design_token_extraction","value":"tokens extracted","source_ids":["figma_m3_kit"],"details":{}}])
    need(any("figma_m3_kit is inaccessible" in f for p in x["policy_results"] for f in p["findings"]),"D Figma claim not flagged"); passed.append("D Figma blocked")
    # E: silently regenerating baseline fails.
    x,_,_=result("Implement Roborazzi screenshot tests.",claims=[{"type":"screenshot_baseline_update","value":"updated","details":{"automatic_to_silence_failure":True}}])
    need(any(p["policy_id"]=="visual_baseline_approval" and p["status"]=="FAIL" for p in x["policy_results"]),"E baseline manipulation not failed"); passed.append("E baseline manipulation")
    # F: performance claim without comparative measurements is unverified.
    x,_,_=result("Investigate Android startup performance.",claims=[{"type":"performance_improvement","value":"startup improved","details":{}}])
    need(x["overall_status"]=="NOT VERIFIED","F unsupported performance claim"); passed.append("F performance claim")
    # G: unknown source id fails validation.
    x,_,_=result("Implement Material 3 color in Compose.",claims=[{"type":"source_content","value":"claim","source_ids":["not_registered"]}])
    need(x["overall_status"]=="FAIL","G unknown source accepted"); passed.append("G provenance")
    # H: discovery is distinct from invocation and reading.
    m=route("Implement a Material 3 color system in Jetpack Compose.")
    with tempfile.TemporaryDirectory() as td:
        trace=Path(td,"codex-discovery.txt")
        proc=subprocess.run([sys.executable,"scripts/check_codex_skill_discovery.py"],cwd=ROOT,capture_output=True,text=True)
        trace.write_text(proc.stdout+proc.stderr,encoding="utf-8")
        discovery=check("codex-skill-metadata-discovery","testing_evidence","PASS" if proc.returncode==0 else "BLOCKED",code=proc.returncode,
            artifact_ref=str(trace),artifact_sha256=hashlib.sha256(trace.read_bytes()).hexdigest())
        e=ev(m,checks=[discovery]); e["skill_evidence"].update({"discovery_check_id":"codex-skill-metadata-discovery","invoked":False,"skill_md_read":False})
        x=q.evaluate(e,m,ROOT)
        se=x["skill_states"][0]
        expected_discovery="PASS" if proc.returncode==0 else "NOT VERIFIED" if proc.returncode==2 else "FAIL"
        need(se["metadata_discovered"]==expected_discovery and se["invoked"]=="NOT VERIFIED" and se["skill_md_read"]=="NOT VERIFIED","H skill states conflated or unavailable discovery overstated")
    passed.append("H metadata discovery observed when available; invocation/read remain distinct")
    # I: workflow configured, no hosted run remains unverified.
    x,_,_=result("Improve Android context routing.",kind="harness_only",hosted_ci={"workflow_exists":True})
    need(x["hosted_ci"]=="NOT VERIFIED","I workflow existence treated as execution"); passed.append("I hosted CI")
    # J: record an actual local validation subprocess, timestamp and output in temp fixture.
    proc=subprocess.run([sys.executable,"scripts/validate_registry.py"],cwd=ROOT,capture_output=True,text=True)
    need(proc.returncode==0,"J actual local registry validation failed")
    with tempfile.TemporaryDirectory() as td:
        artifact=Path(td,"validation-output.txt"); artifact.write_text(proc.stdout+proc.stderr,encoding="utf-8")
        m=route("Improve Android context routing.")
        c=check("actual-registry-validation","testing_evidence",code=proc.returncode,artifact_ref=str(artifact),artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
        evidence=ev(m,kind="harness_only",checks=[c])
        manifest_file=Path(td,"manifest.json"); evidence_file=Path(td,"evidence.json")
        manifest_file.write_text(json.dumps(m,sort_keys=True),encoding="utf-8")
        evidence_file.write_text(json.dumps(evidence,sort_keys=True),encoding="utf-8")
        cli=subprocess.run([sys.executable,"scripts/evaluate_quality_gate.py","--manifest",str(manifest_file),"--evidence",str(evidence_file),"--workspace-root",str(ROOT)],cwd=ROOT,capture_output=True,text=True)
        need(cli.returncode==3,"J CLI should retain NOT VERIFIED for other unsatisfied task requirements")
        x=json.loads(cli.stdout)
        tr=next(p for p in x["policy_results"] if p["policy_id"]=="testing_evidence")
        need(tr["status"]=="PASS","J actual execution evidence did not pass its scoped policy")
    passed.append("J actual local validation evidence")
    # K: multi-policy requirements merge without duplicate policy ids.
    m=route("Implement Material 3 Expressive accessibility and screenshot validation.")
    ids=[p["id"] for p in m["selected_policies"]]
    need(len(ids)==len(set(ids)) and {"design_compliance","accessibility_review","visual_baseline_approval","testing_evidence"} <= set(ids),"K policy merge incomplete/duplicated"); passed.append("K multi-policy merge")
    # L: same structured evidence and registry -> same logical result.
    m=route("Improve Android context routing."); e=ev(m,kind="harness_only")
    a=q.evaluate(e,m,ROOT); b=q.evaluate(e,m,ROOT)
    need(a==b,"L evaluator is nondeterministic"); passed.append("L deterministic evaluation")
    # M: malformed and inconsistent data is caught; no authenticity claim.
    bad=ev(m,kind="harness_only"); bad["checks"]=[check("forged","testing_evidence",code=8)]
    x=q.evaluate(bad,m,ROOT)
    need(x["overall_status"]=="FAIL","M pass with nonzero exit was not caught")
    malformed=ev(m,kind="harness_only"); malformed["task"].pop("id")
    need(q.evaluate(malformed,m,ROOT)["overall_status"]=="FAIL","M malformed schema not caught")
    bad_time=ev(m,kind="harness_only",checks=[check("bad-time","testing_evidence",observed_at="yesterday")])
    need(q.evaluate(bad_time,m,ROOT)["overall_status"]=="FAIL","M invalid timestamp was not caught")
    blocked_check=check("blocked-tool","testing_evidence","BLOCKED",code=None)
    blocked_check.pop("artifact_ref"); blocked_check.pop("artifact_sha256")
    blocked=ev(m,kind="harness_only",checks=[blocked_check])
    need(q.evaluate(blocked,m,ROOT)["overall_status"]=="BLOCKED","M unavailable tool did not remain BLOCKED")
    unsafe=ev(m,kind="harness_only",claims=[{"type":"destructive_operation","value":"removed files","details":{"authorized":False}}])
    need(q.evaluate(unsafe,m,ROOT)["overall_status"]=="FAIL","M unauthorized destructive operation was not rejected")
    passed.append("M tampering, schema consistency, blocked-state, and security violation detection")
    # N: manual review is a requirement; advisory is never mechanically passed.
    p={"id":"advisory_fixture","enforcement_mode":"advisory_guidance","remediation_guidance":"review"}
    rr=q.policy_result(p,ev(m,kind="harness_only"),m,{}, {}, {"status":"PASS","prohibited_artifacts":[],"credential_filename_candidates":[]})
    design=route("Review Material 3 color and visual design.")
    manual=q.evaluate(ev(design),design,ROOT)
    manual_result=next(x for x in manual["policy_results"] if x["policy_id"]=="design_compliance")
    need(rr["status"]=="ADVISORY" and manual_result["status"]=="NOT VERIFIED","N advisory/manual review was mechanically passed")
    passed.append("N advisory/manual distinction")
    print(f"PASS: {len(passed)}/14 P4 policy/evidence evaluations")
    for name in passed: print(f"PASS: {name}")
    print("NOTE: J records an actual local process result in a temporary fixture; it does not establish hosted CI or cryptographic authenticity.")
if __name__=="__main__": run()
