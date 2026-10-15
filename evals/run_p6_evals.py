#!/usr/bin/env python3
"""P6 regression, synthetic integration, quality precision, and readiness tests."""
from __future__ import annotations
import contextlib,hashlib,importlib.util,io,json,shutil,subprocess,sys,tempfile
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
sys.path.insert(0,str(ROOT/"scripts"));import route_context as router
p5=module("p5_eval_for_p6",ROOT/"evals/run_harness_evals.py")
material=module("material_validator_p6",ROOT/"scripts/validate_material_evidence.py")
release_gate=module("release_gate_p6",ROOT/"scripts/check_release_readiness.py")

def record(out,name,ok,detail):
    out.append({"id":name,"status":"PASS" if ok else "FAIL","detail":detail})
    if not ok:raise AssertionError(f"{name}: {detail}")
def cmd(args,cwd):return subprocess.run([str(x) for x in args],cwd=cwd,capture_output=True,text=True)
def tree_copy(src:Path,dst:Path):shutil.copytree(src,dst,ignore=shutil.ignore_patterns(".git","__pycache__","*.pyc"))
def file_hash(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def worktree_digest(root:Path)->str:
    digest=hashlib.sha256();ignored={".git","__pycache__"}
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not ignored.intersection(p.relative_to(root).parts) and p.suffix!=".pyc" and p.relative_to(root).as_posix()!="evals/reports/p6-integration-report.json"):
        digest.update(path.relative_to(root).as_posix().encode());digest.update(b"\0");digest.update(path.read_bytes());digest.update(b"\0")
    return digest.hexdigest()

def evaluate_precision()->dict:
    with contextlib.redirect_stdout(io.StringIO()):
        rc=p5.run(output_path=Path(tempfile.gettempdir())/"p6-p5-baseline-report.json")
    if rc:raise AssertionError("independent P5 dataset failed after P6 routing changes")
    after=json.loads((Path(tempfile.gettempdir())/"p6-p5-baseline-report.json").read_text())
    before=json.loads((ROOT/"evals/reports/p5-routing-report.json").read_text())
    domains=("androidx_api","harness","material3_content_design","material3_xr")
    result={}
    for d in domains:
        old=before["per_domain"][d]["knowledge_precision"];new=after["per_domain"][d]["knowledge_precision"]
        result[d]={"p5":old,"p6":new,"delta":round(new-old,4),"cases":after["per_domain"][d]["cases"],"required_knowledge_recall":after["per_domain"][d]["knowledge_recall"],"failures":after["per_domain"][d]["cases_failed"]}
        if new<=old or result[d]["required_knowledge_recall"]<1 or result[d]["failures"]:raise AssertionError(f"knowledge precision did not safely improve for {d}: {result[d]}")
    result["aggregate"]={"p5":before["aggregate"],"p6":after["aggregate"]}
    return result

def integration_checks(results:list)->dict:
    with tempfile.TemporaryDirectory(prefix="android-context-independent-target-") as td:
        target=Path(td)/"sample-android-repo";target.mkdir();harness=target/".codex/android-context-harness";harness.parent.mkdir(parents=True)
        tree_copy(ROOT,harness)
        agents=target/"AGENTS.md";agents.write_text("# Product instructions\n\nArchitecture: single app module, constructor injection only.\n",encoding="utf-8")
        sentinel=target/"product-data.txt";sentinel.write_text("user-owned-product-data\n",encoding="utf-8");sentinel_hash=file_hash(sentinel)
        dev_block=cmd([sys.executable,harness/"scripts/integrate_harness.py","--action","install","--target",target,"--harness-root",harness],ROOT)
        record(results,"A_development_channel_guard",dev_block.returncode==2 and not (target/".codex/android-context-integration.json").exists() and "Product instructions" in agents.read_text(),"Unreleased development channel is rejected unless an explicit isolated-test flag is supplied.")
        result=cmd([sys.executable,harness/"scripts/integrate_harness.py","--action","install","--target",target,"--harness-root",harness,"--allow-development"],ROOT)
        if result.returncode:raise AssertionError(f"clean integration failed: {result.stdout}{result.stderr}")
        state_path=target/".codex/android-context-integration.json";state=json.loads(state_path.read_text())
        selected_skill=target/".agents/skills/material3-expressive/SKILL.md"
        record(results,"A_clean_integration",state["harness_version"]=="0.6.0-dev" and selected_skill.is_file() and not (target/"knowledge").exists(),"Separate harness checkout, native skill files, and project config installed; knowledge remains in harness checkout.")
        preserved=agents.read_text().startswith("# Product instructions") and sentinel.read_text()=="user-owned-product-data\n" and file_hash(sentinel)==sentinel_hash
        record(results,"B_project_isolation",preserved,"Existing AGENTS.md instructions and unrelated product data remained intact.")
        project_path=target/".codex/android-project-context.json";project=json.loads(project_path.read_text())
        api_task="Use MaterialShapes in a Compose component."
        no_versions=cmd([sys.executable,harness/"scripts/route_context.py",api_task,"--project-config",project_path],harness)
        if no_versions.returncode:raise AssertionError(f"empty project context routing failed: {no_versions.stderr}")
        no_versions_manifest=json.loads(no_versions.stdout)
        missing_version_warning=any("dependency declarations are absent" in x for x in no_versions_manifest["required_verification_actions"])
        project["project_id"]="synthetic-target-only";project["androidx_dependencies"]={"androidx.compose.material3:material3":"synthetic-declared-version"};project["architecture_constraints"]=["No DI framework; use constructor injection."]
        project["source_files_observed"]=["synthetic-fixture-project-context"]
        project_path.write_text(json.dumps(project,indent=2)+"\n",encoding="utf-8")
        task="Review dependency injection architecture with Hilt."
        routed=cmd([sys.executable,harness/"scripts/route_context.py",task,"--project-config",project_path],harness)
        if routed.returncode:raise AssertionError(f"project-config router failed: {routed.stderr}")
        manifest=json.loads(routed.stdout)
        c=manifest["target_project_context"]
        record(results,"C_project_versions",missing_version_warning and c["androidx_dependencies"].get("androidx.compose.material3:material3")=="synthetic-declared-version" and c["status"]=="provided_declarations_not_independently_verified" and any("resolved AndroidX" in x for x in manifest["required_verification_actions"]),"Missing versions are flagged; synthetic declarations are visible but remain unverified and still require resolved dependency evidence.")
        record(results,"D_project_conflict",c["architecture_constraints"]==["No DI framework; use constructor injection."] and any("explicit project-owner decision" in x for x in manifest["required_verification_actions"]),"Conflicting generic Hilt guidance is surfaced for an explicit owner decision; no project architecture was changed.")
        # Incompatible schema must fail before touching AGENTS or installed skills.
        skill_hash=file_hash(selected_skill);agents_hash=file_hash(agents);state_hash=file_hash(state_path)
        rel=harness/"release/harness-manifest.json";release=json.loads(rel.read_text());release["schemas"]["context_manifest"]=99;rel.write_text(json.dumps(release,indent=2)+"\n")
        incompatible=cmd([sys.executable,harness/"scripts/integrate_harness.py","--action","upgrade","--target",target,"--harness-root",harness,"--allow-development"],ROOT)
        unchanged=all([file_hash(selected_skill)==skill_hash,file_hash(agents)==agents_hash,file_hash(state_path)==state_hash])
        record(results,"I_incompatible_schema",incompatible.returncode==2 and unchanged,"Unsupported schema set blocks upgrade before modifying target files.")
        release["schemas"]["context_manifest"]=2;release["harness_version"]="0.6.1-dev";rel.write_text(json.dumps(release,indent=2)+"\n")
        # Controlled source change proves an upgrade is reversible.
        src_skill=harness/".agents/skills/material3-expressive/SKILL.md";old_source=src_skill.read_text();src_skill.write_text(old_source+"\nSynthetic reversible upgrade fixture.\n")
        upgrade=cmd([sys.executable,harness/"scripts/integrate_harness.py","--action","upgrade","--target",target,"--harness-root",harness,"--allow-development"],ROOT)
        if upgrade.returncode:raise AssertionError(f"synthetic upgrade failed: {upgrade.stdout}{upgrade.stderr}")
        upgraded=json.loads(state_path.read_text());is_upgraded=upgraded["harness_version"]=="0.6.1-dev" and "Synthetic reversible upgrade fixture" in selected_skill.read_text()
        rollback=cmd([sys.executable,harness/"scripts/integrate_harness.py","--action","rollback","--target",target],ROOT)
        if rollback.returncode:raise AssertionError(f"upgrade rollback failed: {rollback.stdout}{rollback.stderr}")
        rolled=json.loads(state_path.read_text());restored=rolled["harness_version"]=="0.6.0-dev" and file_hash(selected_skill)==skill_hash and "0.6.0-dev" in agents.read_text()
        record(results,"J_upgrade_rollback",is_upgraded and rollback.returncode==0 and restored,"0.6.1-dev synthetic update rolled back to the previous installed version and skill bytes.")
        first_rollback=cmd([sys.executable,harness/"scripts/integrate_harness.py","--action","rollback","--target",target],ROOT)
        preserved_after_refusal=first_rollback.returncode==2 and state_path.exists() and project_path.exists() and sentinel.read_text()=="user-owned-product-data\n" and "managed integration" in agents.read_text()
        record(results,"J_rollback_preserves_user_edits",preserved_after_refusal,"Rollback refused to delete the user-edited project context and made no partial removal.")
        clean_target=Path(td)/"clean-target";clean_target.mkdir();clean_harness=clean_target/".codex/android-context-harness";clean_harness.parent.mkdir(parents=True);tree_copy(ROOT,clean_harness)
        clean_agents=clean_target/"AGENTS.md";clean_agents.write_text("# Existing instructions\n",encoding="utf-8")
        clean_install=cmd([sys.executable,clean_harness/"scripts/integrate_harness.py","--action","install","--target",clean_target,"--harness-root",clean_harness,"--allow-development"],ROOT)
        clean_rollback=cmd([sys.executable,clean_harness/"scripts/integrate_harness.py","--action","rollback","--target",clean_target],ROOT)
        clean_ok=clean_install.returncode==0 and clean_rollback.returncode==0 and not (clean_target/".codex/android-context-integration.json").exists() and not (clean_target/".codex/android-project-context.json").exists() and clean_agents.read_text()=="# Existing instructions\n"
        record(results,"J_clean_install_rollback",clean_ok,f"install={clean_install.returncode} rollback={clean_rollback.returncode} state={(clean_target/'.codex/android-context-integration.json').exists()} config={(clean_target/'.codex/android-project-context.json').exists()} agents={clean_agents.read_text()!r} rollback_output={clean_rollback.stderr}")
        forbidden=[p.name for p in target.rglob("*") if p.is_file() and p.suffix.lower() in {".apk",".aab"} or p.name in {"build.gradle","build.gradle.kts","settings.gradle","settings.gradle.kts","AndroidManifest.xml"}]
        record(results,"A_no_android_generation",not forbidden,f"Prohibited Android artifacts: {forbidden}")
        return {"status":"PASS","target_root":"temporary fixture; removed after test","harness_version":"0.6.0-dev","installed_native_skill_files":sum(1 for x in state["skills"].values() if x["owned"]),"shared_knowledge_copied":False}

def main()->int:
    results=[]
    precision=evaluate_precision()
    record(results,"E_knowledge_precision",all(precision[d]["p6"]>precision[d]["p5"] and precision[d]["required_knowledge_recall"]==1 for d in ("androidx_api","harness","material3_content_design","material3_xr")),json.dumps({d:precision[d] for d in ("androidx_api","harness","material3_content_design","material3_xr")},sort_keys=True))
    integration=integration_checks(results)
    topics=json.loads((ROOT/"routing/material3-topics.json").read_text())["topics"]
    sitemap=json.loads((ROOT/"routing/material3-sitemap-evidence.json").read_text())["urls"]
    evidence=json.loads((ROOT/"routing/material3-retrieval-evidence.json").read_text())
    coverage=material.validate_records(evidence,topics,sitemap)
    unread=[u for u in sitemap if u not in {r["canonical_url"] for r in evidence["records"]}]
    record(results,"F_discovered_not_verified",len(topics)==21 and len(sitemap)==249 and coverage["verified_page_content_topics"]==0 and len(unread)>0,"21 topic groups/249 URLs discovered; sampled shell retrievals are not page-content verification.")
    bogus=json.loads(json.dumps(evidence));bogus["records"][0].update({"state":"verified","verified":True,"page_content_obtained":True})
    try:material.validate_records(bogus,topics,sitemap);g=False;detail="false VERIFIED claim was accepted"
    except ValueError as e:g=True;detail=str(e)
    record(results,"G_retrieval_requires_attribution",g,detail)
    # The P4 test invokes the locally available metadata-discovery check and asserts
    # that its observed PASS never changes invocation/body-read from NOT VERIFIED.
    skill_eval=cmd([sys.executable,ROOT/"evals/run_quality_gate_evals.py"],ROOT)
    skill_trace=(skill_eval.stdout+skill_eval.stderr)
    record(results,"H_skill_observability",skill_eval.returncode==0 and "PASS: H metadata discovery observed when available; invocation/read remain distinct" in skill_trace,"Actual discovery check is consumed by the existing P4 evaluator; invocation and SKILL.md reading remain separate NOT VERIFIED states.")
    native_probe=cmd([sys.executable,ROOT/"scripts/check_codex_skill_discovery.py"],ROOT)
    native_discovery="PASS" if native_probe.returncode==0 and "exposed the material3-expressive activation description" in native_probe.stdout else "NOT VERIFIED" if native_probe.returncode==2 else "FAIL"
    readiness=release_gate.readiness(ROOT)
    vc_expected=("PASS" if readiness["head"] and readiness["tracked_file_count"]>0 and readiness["working_tree_clean"] and readiness["remote"] else "BLOCKED")
    record(results,"K_release_readiness_blocked",readiness["release_ready"]=="BLOCKED" and readiness["version_control_ready"]==vc_expected and readiness["hosted_ci"] in {"PASS","FAIL","NOT VERIFIED"} and readiness["material_source_verification"]!="PASS",f"Release remains {readiness['release_ready']}; version control={readiness['version_control_ready']} (expected {vc_expected} from observed Git state); hosted CI={readiness['hosted_ci']}; Material source verification={readiness['material_source_verification']}. A real CI PASS does not bypass the still-blocked Material.io source gate.")
    # Full pre-P6 regression gate; bootstrap deliberately excludes this runner to avoid recursion.
    regress=cmd(["bash",ROOT/"scripts/bootstrap-cloud.sh"],ROOT)
    record(results,"L_p0_p5_regressions",regress.returncode==0,(regress.stdout+regress.stderr)[-1200:])
    head=cmd(["git","rev-parse","--verify","HEAD"],ROOT)
    report={"schema_version":1,"harness_version":json.loads((ROOT/"release/harness-manifest.json").read_text())["harness_version"],"git_head":head.stdout.strip() if head.returncode==0 else None,"working_tree_sha256":worktree_digest(ROOT),"status":"PASS" if all(x["status"]=="PASS" for x in results) else "FAIL","evaluations":results,"precision_comparison":precision,"synthetic_integration":integration,"material_coverage":coverage,"retrieval_records":evidence["records"],"native_codex_skill_discovery":native_discovery,"native_codex_skill_invocation":"NOT VERIFIED","hosted_ci":readiness["hosted_ci"],"release_readiness":readiness}
    try:
        from jsonschema import Draft202012Validator
        schema=json.loads((ROOT/"evals/schemas/p6-evaluation-report.schema.json").read_text())
        errors=sorted(Draft202012Validator(schema).iter_errors(report),key=lambda e:list(map(str,e.path)))
        if errors:raise AssertionError("P6 report schema invalid: "+"; ".join(e.message for e in errors[:6]))
    except ImportError as e:raise AssertionError("jsonschema is required to validate the P6 result") from e
    out=ROOT/"evals/reports/p6-integration-report.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    # The report itself is excluded from the digest, so the final readiness snapshot
    # can independently confirm that these integration results still match this tree.
    report["release_readiness"]=release_gate.readiness(ROOT)
    report["hosted_ci"]=report["release_readiness"]["hosted_ci"]
    report["working_tree_sha256"]=worktree_digest(ROOT)
    report["status"]="PASS" if all(x["status"]=="PASS" for x in results) else "FAIL"
    errors=sorted(Draft202012Validator(schema).iter_errors(report),key=lambda e:list(map(str,e.path)))
    if errors:raise AssertionError("final P6 report schema invalid: "+"; ".join(e.message for e in errors[:6]))
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(f"P6 evaluations {sum(x['status']=='PASS' for x in results)}/{len(results)} PASS; status {report['status']}")
    for x in results:print(f"{x['status']} {x['id']}: {x['detail'][:380]}")
    print(f"Report: {out}")
    return 0 if report["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
