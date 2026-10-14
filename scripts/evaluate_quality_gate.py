#!/usr/bin/env python3
"""Evaluate structured harness evidence with fixed rules; registry text is never executed."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATES = {"PASS", "FAIL", "BLOCKED", "NOT VERIFIED"}
RULE_BY_POLICY = {
    "provenance":"source_provenance", "source_access":"source_access_claims", "api_compatibility":"api_compatibility",
    "experimental_api":"experimental_api", "design_compliance":"manual_design_review", "architecture_boundaries":"manual_architecture_review",
    "dependency_selection":"dependency_selection", "scope_isolation":"scope_isolation", "visual_baseline_approval":"visual_baseline_approval",
    "measurement_first":"measurement_first", "performance_claims":"performance_claims", "reporting":"reporting_integrity",
    "api_verification":"api_verification", "security":"security_artifacts", "freshness":"source_freshness",
    "no_hallucinated_api":"api_claim_provenance", "testing_evidence":"testing_execution", "accessibility_review":"manual_accessibility_review"
}

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def validate_schema(value: Any, schema_path: Path) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["BLOCKED: jsonschema dependency is unavailable"]
    errors = sorted(Draft202012Validator(read_json(schema_path), format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(value), key=lambda e: list(map(str, e.path)))
    return [f"{'.'.join(map(str, e.path)) or '$'}: {e.message}" for e in errors]

def scan_workspace(root: Path) -> dict:
    blocked, credentials = [], []
    if not root.exists() or not root.is_dir():
        return {"status": "BLOCKED", "reason": "workspace root unavailable", "prohibited_artifacts": [], "credential_filename_candidates": []}
    ignored = {".git", "__pycache__", ".venv", "venv", "node_modules"}
    credential_names = {".env", "service-account.json", "credentials.json"}
    for p in sorted(root.rglob("*")):
        if any(part in ignored for part in p.relative_to(root).parts):
            continue
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        low = p.name.lower()
        if low.endswith((".apk", ".aab")) or p.name == "AndroidManifest.xml" or (p.name in {"settings.gradle", "settings.gradle.kts", "build.gradle", "build.gradle.kts"}):
            blocked.append(rel)
        if low in credential_names or low.endswith((".jks", ".keystore", ".p12", ".pem")):
            credentials.append(rel)
    return {"status": "PASS", "prohibited_artifacts": blocked, "credential_filename_candidates": credentials,
            "limitations": ["Filename scan only; does not inspect file contents for secrets."]}

def check_map(ev: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for check in ev.get("checks", []):
        if isinstance(check, dict): out.setdefault(check.get("policy_id", ""), []).append(check)
    return out

def observed(check: dict) -> bool:
    return check.get("evidence_origin") in {"observed_tool_output", "observed_artifact", "human_review"} and bool(check.get("observed_at"))

def policy_result(policy: dict, ev: dict, manifest: dict, sources: dict, checks: dict, scan: dict) -> dict:
    pid, mode = policy["id"], policy["enforcement_mode"]
    findings: list[str] = []
    status = "PASS"
    relevant = checks.get(pid, [])
    observed_checks = [c for c in relevant if observed(c)]
    claims = ev.get("claims", [])
    if mode == "manual_review":
        observed_checks = [c for c in observed_checks if c.get("evidence_origin") == "human_review" and c.get("details", {}).get("reviewer") and c.get("details", {}).get("review_result")]
    def setstate(s: str, message: str):
        nonlocal status
        rank = {"PASS": 0, "ADVISORY": 0, "NOT VERIFIED": 1, "BLOCKED": 2, "FAIL": 3}
        if rank[s] > rank[status]: status = s
        findings.append(message)

    if mode == "advisory_guidance":
        return {"policy_id": pid, "status": "ADVISORY", "enforcement_mode": mode, "findings": ["Advisory guidance; no mechanical compliance claim made."], "remediation": policy["remediation_guidance"]}
    # Explicit observed policy check can establish result only when evidence is observed.
    if observed_checks:
        for c in observed_checks:
            if c["status"] == "FAIL": setstate("FAIL", f"Observed check {c['id']} failed.")
            elif c["status"] == "BLOCKED": setstate("BLOCKED", f"Observed check {c['id']} was blocked.")
            elif c["status"] == "NOT VERIFIED": setstate("NOT VERIFIED", f"Observed check {c['id']} did not verify the requirement.")
            elif c["status"] == "PASS": findings.append(f"Observed check {c['id']} passed.")
    elif mode == "manual_review":
        setstate("NOT VERIFIED", "Manual review evidence with reviewer and outcome is required.")

    if pid == "provenance":
        source_ids = {s.get("id") for s in manifest.get("selected_sources", [])}
        known = set(sources)
        unknown = source_ids - known
        if unknown: setstate("FAIL", f"Unknown source identifiers: {sorted(unknown)}")
        for ref in manifest.get("selected_knowledge_references", []):
            ref_sources = set(ref.get("source_ids", []))
            path = ref.get("path", "")
            if ref_sources and not ref_sources <= known: setstate("FAIL", "Knowledge reference has unknown source provenance.")
            if not ref_sources and not (path.startswith("docs/") or path == "knowledge/README.md"):
                setstate("NOT VERIFIED", f"Knowledge reference has no external source IDs; repository-authored context is allowed only for designated docs: {path}")
            target = (ROOT / path).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file(): setstate("FAIL", f"Unresolved or unsafe knowledge path: {path}")
        if not findings: findings.append("Selected sources and knowledge references resolve to registry records and local files.")
    if pid == "scope_isolation" and ev.get("task", {}).get("kind") == "harness_only":
        if scan.get("status") == "BLOCKED": setstate("BLOCKED", scan["reason"])
        elif scan["prohibited_artifacts"]: setstate("FAIL", f"Harness-only workspace contains prohibited Android artifacts: {scan['prohibited_artifacts']}")
        elif status == "PASS": findings.append("Workspace scan found no Android project/build artifacts.")
    if pid == "security" and scan.get("credential_filename_candidates"):
        setstate("NOT VERIFIED", "Potential credential/signing filenames require review; file contents were not inspected.")
    if pid == "security":
        for claim in claims:
            if claim.get("type") not in {"destructive_operation", "release_signing_change", "external_dependency_install"}: continue
            if claim.get("details", {}).get("authorized") is False:
                setstate("FAIL", f"Unauthorized {claim['type']} was reported."); continue
            linked = set(claim.get("evidence_check_ids", []))
            approvals = [c for c in ev.get("checks", []) if c.get("id") in linked and observed(c) and c.get("evidence_origin") == "human_review" and c.get("details", {}).get("reviewer") and c.get("details", {}).get("explicit_approval") is True]
            if not approvals: setstate("NOT VERIFIED", f"{claim['type']} requires an observed explicit human approval record.")
    if pid == "testing_evidence":
        usable = [c for c in ev.get("checks", []) if observed(c) and c.get("exit_code") is not None and c.get("command_or_tool") and (c.get("artifact_ref") or c.get("verification_result"))]
        if not usable: setstate("NOT VERIFIED", "No executed check with observed command, exit code, timestamp, and output evidence.")
        elif any(c.get("status") == "FAIL" or (c.get("status") == "PASS" and c.get("exit_code") != 0) for c in usable): setstate("FAIL", "Check status conflicts with its observed exit code or reports failure.")
        elif not findings: findings.append(f"{len(usable)} executed check(s) have observable evidence.")
    if pid == "reporting":
        bad = [c.get("id") for c in ev.get("checks", []) if c.get("evidence_origin") == "reported_assertion" and c.get("status") == "PASS"]
        if bad: setstate("NOT VERIFIED", f"Reported PASS assertions lack observed execution evidence: {bad}")
        elif not findings: findings.append("Reported outcomes are not presented as observed without evidence.")
    if pid in {"api_compatibility", "api_verification", "experimental_api", "no_hallucinated_api"}:
        api_claims = [c for c in claims if c.get("type") in {"api_signature", "api_usage", "experimental_api"}]
        for claim in api_claims:
            api_source_ids = set(claim.get("source_ids", []))
            selected_source_ids = {s.get("id") for s in manifest.get("selected_sources", [])}
            if not api_source_ids or any(sid not in sources for sid in api_source_ids):
                setstate("FAIL", "API claim lacks registered source provenance.")
            elif not api_source_ids <= selected_source_ids or any(sources[sid].get("authority_level") != "official_api_contract" for sid in api_source_ids):
                setstate("FAIL", "API claim must cite selected official AndroidX/API contract sources.")
            evidence_ids = set(claim.get("evidence_check_ids", []))
            observations = [c for c in ev.get("checks", []) if c.get("id") in evidence_ids and observed(c) and c.get("status") == "PASS"]
            details = [c.get("details", {}) for c in observations]
            if claim.get("details", {}).get("verification_unavailable") or any(d.get("verification_unavailable") for d in details):
                setstate("BLOCKED", "Official API/version verification resource or tool is unavailable.")
            elif not any(d.get("api_name") and d.get("target_artifact") and d.get("resolved_version") and d.get("current_official_source_verified") is True for d in details):
                setstate("NOT VERIFIED", "Exact API, target artifact/version, and current official-source compatibility evidence are required from an observed check.")
            if claim.get("type") == "experimental_api" and not any(d.get("opt_in_annotation") and d.get("opt_in_reviewed") is True for d in details):
                setstate("NOT VERIFIED", "Experimental API opt-in annotation and narrow-scope review are required from an observed check.")
        if not api_claims and pid in {"api_compatibility", "api_verification", "experimental_api"}:
            setstate("NOT VERIFIED", "The selected API policy requires an explicit API/version compatibility assessment; none was supplied.")
    if pid == "source_access":
        for claim in claims:
            if claim.get("type") not in {"source_content", "design_token_extraction", "page_specific_design_claim"}: continue
            for sid in claim.get("source_ids", []):
                src = sources.get(sid)
                if not src: setstate("FAIL", f"Claim uses unknown source identifier {sid}."); continue
                if src.get("accessibility_status") in {"blocked", "inaccessible", "partial_js_shell", "sitemap_only", "metadata_only", "blocked_403"}:
                    evidence_ids = claim.get("evidence_check_ids", [])
                    export = any(c.get("id") in evidence_ids and observed(c) and c.get("evidence_origin") == "observed_artifact" and c.get("artifact_ref") and c.get("details", {}).get("authorized_export") is True for c in ev.get("checks", []))
                    if not export: setstate("NOT VERIFIED", f"{sid} is inaccessible/partial; observed page or authorized export evidence is required.")
    if pid == "visual_baseline_approval":
        for claim in claims:
            if claim.get("type") == "screenshot_baseline_update":
                if claim.get("details", {}).get("automatic_to_silence_failure"):
                    setstate("FAIL", "Baseline was automatically changed to silence a failing comparison.")
                approvals = [c for c in ev.get("checks", []) if c.get("policy_id") == pid and observed(c) and c.get("evidence_origin") == "human_review" and c.get("details", {}).get("reviewer") and c.get("details", {}).get("explicit_approval") is True]
                if not approvals: setstate("NOT VERIFIED", "Baseline updates require an observed reviewer and explicit approval.")
    if pid == "performance_claims":
        for claim in claims:
            if claim.get("type") != "performance_improvement": continue
            evidence_ids = set(claim.get("evidence_check_ids", []))
            measurements = [c for c in ev.get("checks", []) if c.get("id") in evidence_ids and observed(c) and c.get("status") == "PASS" and c.get("command_or_tool")]
            required = ("baseline", "comparison", "metric", "device", "build_variant", "workload", "run_counts")
            if not any(all(c.get("details", {}).get(k) for k in required) for c in measurements): setstate("NOT VERIFIED", "Performance improvement lacks an observed check containing comparable baseline, metric, device/build, workload, and run-count measurements.")
    if pid == "measurement_first":
        if any(c.get("type") == "performance_improvement" for c in claims) and not any(c.get("policy_id") == pid and observed(c) and c.get("status") == "PASS" for c in ev.get("checks", [])):
            setstate("NOT VERIFIED", "Measurement-first work requires an observed repeatable baseline check.")
    if pid == "freshness":
        required = {x.get("source_id") for x in manifest.get("freshness", {}).get("source_records", []) if x.get("live_verification_required")}
        verified = set()
        for c in observed_checks:
            if c.get("status") == "PASS": verified.update(c.get("details", {}).get("source_ids", []))
        missing = required - verified
        if missing: setstate("NOT VERIFIED", f"Live verification is still required for selected sources: {sorted(missing)}")
    if pid == "source_access" and status == "PASS" and not any(c.get("type") in {"source_content", "design_token_extraction", "page_specific_design_claim"} for c in claims):
        findings.append("No source-content claim requires access validation.")
    if mode == "runtime_tool_dependent" and not observed_checks and not findings:
        setstate("NOT VERIFIED", "A selected runtime/tool-dependent requirement has no observed verification check.")
    if not findings: findings.append("No deterministic violation found; applicable evidence requirements are met.")
    return {"policy_id": pid, "status": status, "enforcement_mode": mode, "findings": sorted(set(findings)), "remediation": policy["remediation_guidance"]}

def evaluate(evidence: dict, manifest: dict, workspace_root: Path | None = None) -> dict:
    errors = validate_schema(evidence, ROOT / "policies/evidence.schema.json")
    errors += validate_schema(manifest, ROOT / "routing/context-manifest.schema.json")
    try:
        sources_doc, policy_doc, taxonomy = read_json(ROOT / "registry/sources.json"), read_json(ROOT / "registry/policies.json"), read_json(ROOT / "routing/task-taxonomy.json")
        sources = {s["id"]: s for s in sources_doc["sources"]}; policies = {p["id"]: p for p in policy_doc["policies"]}
        selected = {p["id"] for p in manifest.get("selected_policies", [])}
        mandatory = set(taxonomy["global_policy_ids"])
        for pid, expected_rule in RULE_BY_POLICY.items():
            configured = policies.get(pid, {}).get("evaluation", {}).get("rule_id")
            if configured != expected_rule: errors.append(f"policy evaluator mapping mismatch for {pid}: expected {expected_rule}, got {configured}")
        evidence_ids = set(evidence.get("applicable_policy_ids", []))
        if evidence_ids != selected: errors.append("applicable_policy_ids must exactly match manifest selected_policies")
        if not mandatory <= selected: errors.append(f"manifest omitted mandatory global policies: {sorted(mandatory-selected)}")
        unknown = evidence_ids - set(policies)
        if unknown: errors.append(f"unknown policy identifiers: {sorted(unknown)}")
        manifest_sources = {s.get("id") for s in manifest.get("selected_sources", [])}
        unknown_sources = manifest_sources - set(sources)
        if unknown_sources: errors.append(f"unknown source identifiers in context manifest: {sorted(unknown_sources)}")
        registered_skills = {x["id"] for x in read_json(ROOT / "registry/skills.json")["skills"]}
        selected_skills = {x.get("id") for x in manifest.get("selected_skills", [])}
        skill_ids = [x for x in evidence.get("skill_evidence", {}).get("skill_id", "").split(",") if x]
        if set(skill_ids) - registered_skills: errors.append(f"unknown skill identifiers: {sorted(set(skill_ids)-registered_skills)}")
        if set(skill_ids) - selected_skills: errors.append(f"skill evidence names skills not recommended by manifest: {sorted(set(skill_ids)-selected_skills)}")
        check_ids = {x.get("id") for x in evidence.get("checks", []) if isinstance(x, dict)}
        se = evidence.get("skill_evidence", {})
        for field in ("discovery_check_id", "invocation_check_id", "skill_read_check_id", "external_check_id"):
            ref = se.get(field)
            if ref and ref not in check_ids: errors.append(f"skill evidence {field} references missing check {ref}")
        missing_read_checks = set(se.get("knowledge_read_check_ids", [])) - check_ids
        if missing_read_checks: errors.append(f"knowledge read evidence references missing checks: {sorted(missing_read_checks)}")
        digest = "sha256:" + hashlib.sha256(canonical(manifest)).hexdigest()
        if evidence.get("context_manifest_digest") != digest: errors.append("context_manifest_digest does not match the supplied manifest")
        for c in evidence.get("claims", []):
            invalid = set(c.get("source_ids", [])) - set(sources)
            if invalid: errors.append(f"claim has unknown source identifiers: {sorted(invalid)}")
        for c in evidence.get("checks", []):
            if c.get("policy_id") not in policies: errors.append(f"check {c.get('id')} references unknown policy")
            if c.get("observed_at"):
                try:
                    from datetime import datetime
                    observed_time = datetime.fromisoformat(c["observed_at"].replace("Z", "+00:00"))
                    if observed_time.tzinfo is None: errors.append(f"check {c.get('id')} timestamp must include a timezone")
                except (ValueError, TypeError): errors.append(f"check {c.get('id')} has an invalid observed_at timestamp")
            if c.get("status") == "PASS" and c.get("exit_code") not in (None, 0): errors.append(f"check {c.get('id')} claims PASS with nonzero exit code")
            if c.get("artifact_ref") and c.get("artifact_sha256"):
                p = Path(c["artifact_ref"])
                if not p.is_absolute(): p = (ROOT / p).resolve()
                if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() != c["artifact_sha256"]: errors.append(f"artifact digest mismatch for check {c.get('id')}")
                elif not p.is_file(): errors.append(f"NOT VERIFIED: evidence artifact is unavailable: {c['artifact_ref']}")
        if errors:
            return make_result(evidence, [], errors, {"status": "NOT SCANNED", "prohibited_artifacts": [], "credential_filename_candidates": []}, hosted_status(evidence), [])
        scan = scan_workspace(workspace_root or Path(evidence.get("workspace_root", ROOT)))
        results = [policy_result(policies[pid], evidence, manifest, sources, check_map(evidence), scan) for pid in sorted(selected)]
        skill_states = []
        for skill in evidence.get("skill_evidence", {}).get("skill_id", "").split(","):
            if not skill: continue
            registered = any(s["id"] == skill for s in read_json(ROOT / "registry/skills.json")["skills"])
            se = evidence["skill_evidence"]
            def observed_state(flag, check_ref):
                evidence_checks = {c.get("id"): c for c in evidence.get("checks", []) if isinstance(c, dict)}
                check = evidence_checks.get(se.get(check_ref))
                return "PASS" if flag and check and observed(check) and check.get("status") == "PASS" else "NOT VERIFIED"
            skill_states.append({"skill_id": skill, "registered": registered, "recommended": skill in selected_skills,
                                 "metadata_discovered": observed_state(se.get("metadata_discovered"), "discovery_check_id"),
                                 "invoked": observed_state(se.get("invoked"), "invocation_check_id"),
                                 "skill_md_read": observed_state(se.get("skill_md_read"), "skill_read_check_id"),
                                 "knowledge_references_read": [{"path": path, "status": "PASS" if any(c.get("id") in se.get("knowledge_read_check_ids", []) and observed(c) and c.get("status") == "PASS" and path in c.get("details", {}).get("knowledge_references", []) for c in evidence.get("checks", [])) else "NOT VERIFIED"} for path in se.get("knowledge_references_read", [])],
                                 "external_source_verified": observed_state(se.get("external_source_verified"), "external_check_id")})
        return make_result(evidence, results, [], scan, hosted_status(evidence), skill_states)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return make_result(evidence, [], [f"evaluator input/configuration error: {exc}"], {"status": "NOT SCANNED", "prohibited_artifacts": [], "credential_filename_candidates": []}, hosted_status(evidence), [])

def hosted_status(ev: dict) -> str:
    ci = ev.get("hosted_ci", {})
    if ci.get("workflow_exists") and not ci.get("run_url"): return "NOT VERIFIED"
    if ci.get("run_status") in STATES: return ci["run_status"]
    return "NOT APPLICABLE" if not ci.get("workflow_exists") else "NOT VERIFIED"

def make_result(ev: dict, results: list, errors: list, scan: dict, ci: str, skills: list) -> dict:
    statuses = [r["status"] for r in results if r["status"] != "ADVISORY"]
    scope = ev.get("task", {}).get("completion_scope", "local")
    if scope in {"merge", "release"} and ci != "PASS":
        statuses.append(ci if ci in {"FAIL", "BLOCKED"} else "NOT VERIFIED")
    if errors:
        if any(e.startswith("FAIL:") or not e.startswith(("BLOCKED:", "NOT VERIFIED:")) for e in errors): statuses.append("FAIL")
        elif any(e.startswith("BLOCKED:") for e in errors): statuses.append("BLOCKED")
        else: statuses.append("NOT VERIFIED")
    overall = "FAIL" if "FAIL" in statuses else "BLOCKED" if "BLOCKED" in statuses else "NOT VERIFIED" if "NOT VERIFIED" in statuses else "PASS"
    # Local tasks may have irrelevant runtime/manual policies marked conditionally PASS by the evaluator.
    result = {"schema_version": 1, "task_id": ev.get("task", {}).get("id", "unknown"), "overall_status": overall,
              "completion_approved": overall == "PASS", "policy_results": results, "validation_errors": sorted(errors),
              "workspace_scan": scan, "hosted_ci": ci, "skill_states": skills}
    result["determinism_digest"] = hashlib.sha256(canonical(result)).hexdigest()
    return result

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evidence", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--workspace-root", type=Path)
    args = ap.parse_args()
    try:
        result = evaluate(read_json(args.evidence), read_json(args.manifest), args.workspace_root)
    except (OSError, json.JSONDecodeError) as exc:
        prefix = "NOT VERIFIED" if isinstance(exc, OSError) else "FAIL"
        result = make_result({}, [], [f"{prefix}: cannot read input: {exc}"], {"status": "NOT SCANNED", "prohibited_artifacts": [], "credential_filename_candidates": []}, "NOT VERIFIED", [])
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2, "NOT VERIFIED": 3}[result["overall_status"]]

if __name__ == "__main__": raise SystemExit(main())
