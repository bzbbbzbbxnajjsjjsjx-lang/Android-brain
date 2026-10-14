#!/usr/bin/env python3
"""Report distinct validation, integration, version-control, and release readiness states."""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
def run(root:Path,*cmd):return subprocess.run(cmd,cwd=root,capture_output=True,text=True)
def worktree_digest(root:Path)->str:
    digest=hashlib.sha256()
    ignored={".git","__pycache__"}
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not ignored.intersection(p.relative_to(root).parts) and p.suffix!=".pyc" and p.relative_to(root).as_posix()!="evals/reports/p6-integration-report.json"):
        digest.update(path.relative_to(root).as_posix().encode());digest.update(b"\0");digest.update(path.read_bytes());digest.update(b"\0")
    return digest.hexdigest()
def classify_hosted_ci(head_sha:str,runs:list[dict])->str:
    matched=[x for x in runs if x.get("headSha")==head_sha]
    if not matched:return "NOT VERIFIED"
    latest=max(matched,key=lambda x:x.get("createdAt", ""))
    if latest.get("status")!="completed":return "NOT VERIFIED"
    return "PASS" if latest.get("conclusion")=="success" else "FAIL"
def classify_release_candidate(local:str,integration:str,version_control:str,ci:str,source:str,license_review:str)->str:
    return "PASS" if all(x=="PASS" for x in (local,integration,version_control,ci,source,license_review)) else "BLOCKED"
def classify_stable_release(candidate:str,channel:str,tag_present:bool)->str:
    return "PASS" if candidate=="PASS" and channel=="stable" and tag_present else "BLOCKED"
def github_repo_slug(remote:str)->str|None:
    """Extract owner/repository from supported GitHub HTTPS, SSH, or SCP remotes."""
    value=remote.strip()
    if value.startswith("git@github.com:"):
        path=value.split(":",1)[1]
    else:
        parsed=urlparse(value)
        if parsed.hostname!="github.com" or parsed.scheme not in {"https","ssh"}:
            return None
        path=parsed.path.lstrip("/")
    path=path.removesuffix(".git").strip("/")
    parts=path.split("/")
    return "/".join(parts) if len(parts)==2 and all(parts) else None
def readiness(root:Path)->dict:
    release=json.loads((root/"release/harness-manifest.json").read_text())
    topics=json.loads((root/"routing/material3-topics.json").read_text())["topics"]
    material_evidence=json.loads((root/"routing/material3-retrieval-evidence.json").read_text())
    verified_topics={r["topic_id"] for r in material_evidence.get("records",[]) if r.get("state")=="verified" and r.get("verified") is True and r.get("page_content_obtained") is True}
    required_families={"foundations":"material3_foundations","color":"material3_color","typography":"material3_typography","components":"material3_components","accessibility":"material3_accessibility"}
    source_verification={family:("PASS" if topic_id in verified_topics else "BLOCKED") for family,topic_id in required_families.items()}
    source_gate="PASS" if all(v=="PASS" for v in source_verification.values()) else "BLOCKED"
    license_files=[p.name for p in (root/"LICENSE",root/"LICENSE.txt",root/"LICENSE.md") if p.is_file()]
    license_gate="PASS" if license_files and release.get("license_review_status")=="owner_approved" else "OWNER REVIEW REQUIRED" if license_files else "BLOCKED"
    head=run(root,"git","rev-parse","--verify","HEAD")
    tracked=run(root,"git","ls-files")
    status=run(root,"git","status","--porcelain")
    remote=run(root,"git","remote","get-url","origin")
    blockers=[]
    if head.returncode or not head.stdout.strip():blockers.append("Git HEAD is unavailable")
    if tracked.returncode or not tracked.stdout.strip():blockers.append("repository has no tracked baseline files")
    if status.returncode or status.stdout.strip():blockers.append("working tree is not clean against its tracked baseline")
    if release.get("release_channel")!="stable":blockers.append(f"harness release channel is {release.get('release_channel')!r}, not stable")
    if remote.returncode or not remote.stdout.strip():blockers.append("no origin remote is configured")
    ci_status="NOT VERIFIED"
    if remote.returncode==0 and remote.stdout.strip():
        try:
            slug=github_repo_slug(remote.stdout)
            if slug:
                proc=subprocess.run(["gh","run","list","--repo",slug,"--limit","50","--json","status,conclusion,headSha,url,createdAt"],cwd=root,capture_output=True,text=True)
                runs=json.loads(proc.stdout) if proc.returncode==0 else []
                sha=head.stdout.strip() if head.returncode==0 else ""
                ci_status=classify_hosted_ci(sha,runs)
        except (FileNotFoundError,json.JSONDecodeError):ci_status="NOT VERIFIED"
    if ci_status!="PASS":blockers.append(f"hosted CI for the current HEAD is {ci_status}")
    local=run(root,"bash","scripts/bootstrap-cloud.sh")
    local_status="PASS" if local.returncode==0 else "FAIL"
    if local_status!="PASS":blockers.append("local harness validation did not pass")
    integration_report=root/"evals/reports/p6-integration-report.json"
    integration_status="NOT VERIFIED"
    if integration_report.is_file():
        try:
            evidence=json.loads(integration_report.read_text())
            same_tree=evidence.get("working_tree_sha256")==worktree_digest(root)
            integration_status="PASS" if evidence.get("status")=="PASS" and evidence.get("harness_version")==release.get("harness_version") and same_tree else "FAIL" if evidence.get("status")=="FAIL" else "NOT VERIFIED"
        except (OSError,json.JSONDecodeError):integration_status="FAIL"
    if integration_status!="PASS":blockers.append(f"synthetic integration evaluation is {integration_status}")
    tags=run(root,"git","tag","--list",f"v{release.get('harness_version')}")
    if tags.returncode or not tags.stdout.strip():blockers.append("version tag is absent")
    vc_status="PASS" if head.returncode==0 and tracked.returncode==0 and tracked.stdout.strip() and status.returncode==0 and not status.stdout.strip() and remote.returncode==0 else "BLOCKED"
    if source_gate!="PASS":blockers.append("minimum verified Material.io topic-family coverage is not met")
    if license_gate!="PASS": blockers.append("repository-level license is absent or has not received owner approval")
    release_candidate=classify_release_candidate(local_status,integration_status,vc_status,ci_status,source_gate,license_gate)
    stable_release=classify_stable_release(release_candidate,release.get("release_channel"),bool(tags.stdout.strip()))
    return {"local_tested":local_status,"local_validation_ready":local_status,"local_validation_exit_code":local.returncode,"integration_tested":integration_status,"version_control_ready":vc_status,"hosted_ci":ci_status,"material_source_verification":source_gate,"verified_topic_families":source_verification,"required_topic_families":required_families,"repository_license_review":license_gate,"candidate_license_files":license_files,"release_candidate":release_candidate,"stable_release":stable_release,"release_ready":stable_release,"blockers":blockers,"head":head.stdout.strip() if head.returncode==0 else None,"tracked_file_count":len(tracked.stdout.splitlines()) if tracked.returncode==0 else 0,"working_tree_clean":status.returncode==0 and not status.stdout.strip(),"remote":remote.stdout.strip() if remote.returncode==0 else None,"release_version":release.get("harness_version"),"release_channel":release.get("release_channel"),"version_tag_present":bool(tags.stdout.strip()),"material3_verified_topics":len(verified_topics),"material3_registered_topics":len(topics)}
def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--root",type=Path,default=ROOT);a=p.parse_args();r=readiness(a.root.resolve());print(json.dumps(r,indent=2,sort_keys=True));return 2 if r["release_ready"]!="PASS" else 0
if __name__=="__main__":raise SystemExit(main())
