#!/usr/bin/env python3
"""Run destructive configuration mutations only in temporary repository copies."""
from __future__ import annotations
import importlib.util, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("p5_eval", ROOT / "evals/run_harness_evals.py")
p5 = importlib.util.module_from_spec(spec); sys.modules[spec.name] = p5; spec.loader.exec_module(p5)

def load(root: Path, name: str):
    return json.loads((root / name).read_text(encoding="utf-8"))
def save(root: Path, name: str, value):
    (root / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
def copy_repo(dst: Path):
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv"))
def validate(root: Path) -> tuple[bool, str]:
    env = dict(os.environ, ANDROID_HARNESS_ROOT=str(root))
    p = subprocess.run([sys.executable, str(ROOT / "scripts/validate_registry.py")], cwd=ROOT, env=env, text=True, capture_output=True)
    return p.returncode != 0, (p.stdout + p.stderr).strip()
def mutation(name, mutate, structural=True, case_id="mat-color"):
    with tempfile.TemporaryDirectory(prefix="android-harness-p5-mut-") as td:
        root = Path(td) / "repo"; copy_repo(root); mutate(root)
        if structural:
            detected, output = validate(root)
        else:
            # This deliberate route contamination is tested against independently-authored forbidden expectations.
            p5.router.ROOT = root
            data = load(ROOT, "evals/datasets/context_tasks.v1.json")
            case = next(t for t in data["tasks"] if t["id"] == case_id)
            result, _ = p5.evaluate_case(case, set(data["global_required_policies"]), __import__("datetime").date.fromisoformat(data["evaluation_date"]))
            detected, output = not result["passed"], "; ".join(result["failures"])
            p5.router.ROOT = ROOT
        if not detected:
            raise AssertionError(f"mutation escaped detection: {name}; output={output[:300]}")
        return {"id": name, "detected": True, "detector": "registry_validator" if structural else "independent_task_expectations", "evidence": output[:240]}

def main():
    results=[]
    def remove_policy(r):
        d=load(r,"routing/task-taxonomy.json");d["global_policy_ids"].remove("provenance");save(r,"routing/task-taxonomy.json",d)
    results.append(mutation("mandatory_policy_removed",remove_policy))
    def bad_source(r):
        d=load(r,"routing/task-taxonomy.json");d["selection_guidance"][0]["source_ids"][0]="invented_source";save(r,"routing/task-taxonomy.json",d)
    results.append(mutation("source_id_replaced",bad_source))
    def duplicate_source(r):
        d=load(r,"registry/sources.json");d["sources"].append(dict(d["sources"][0]));save(r,"registry/sources.json",d)
    results.append(mutation("conflicting_duplicate_source",duplicate_source))
    def bad_path(r):
        d=load(r,"routing/task-taxonomy.json");d["selection_guidance"][0]["knowledge"][0]="knowledge/missing.md";save(r,"routing/task-taxonomy.json",d)
    results.append(mutation("broken_local_reference",bad_path))
    def broken_provenance(r):
        d=load(r,"registry/sources.json");s=d["sources"][0];p=r/s["local_knowledge_reference"];p.write_text(p.read_text(encoding="utf-8").replace(s["id"],"unknown-source",1),encoding="utf-8")
    results.append(mutation("source_note_provenance_removed",broken_provenance))
    def misclassify(r):
        d=load(r,"registry/sources.json");s=next(x for x in d["sources"] if x["id"]=="material_shapes_api");s["source_type"]="design_specification";save(r,"registry/sources.json",d)
    results.append(mutation("androidx_api_misclassified",misclassify))
    def remove_topic(r):
        d=load(r,"routing/material3-topics.json");d["topics"].pop();save(r,"routing/material3-topics.json",d)
    results.append(mutation("material_topic_removed",remove_topic))
    def disable_provenance(r):
        d=load(r,"registry/policies.json");p=next(x for x in d["policies"] if x["id"]=="provenance");p["enforcement_mode"]="advisory_guidance";save(r,"registry/policies.json",d)
    results.append(mutation("provenance_policy_weakened",disable_provenance))
    def weaken_skill(r):
        d=load(r,"routing/material3-topics.json");t=next(x for x in d["topics"] if x["id"]=="material3_color");t["skill_ids"].remove("material3-expressive");save(r,"routing/material3-topics.json",d)
    results.append(mutation("material_skill_selection_weakened",weaken_skill))
    def assert_figma(r):
        d=load(r,"registry/sources.json");s=next(x for x in d["sources"] if x["id"]=="figma_m3_kit");s["accessibility_status"]="retrieved";save(r,"registry/sources.json",d)
    results.append(mutation("inaccessible_figma_marked_verified",assert_figma,structural=False,case_id="figma-tokens"))
    def contaminate(r):
        d=load(r,"routing/task-taxonomy.json");t=next(x for x in d["selection_guidance"] if x["id"]=="material3_color");t["source_ids"].append("hilt_android");save(r,"routing/task-taxonomy.json",d)
    results.append(mutation("unrelated_source_contamination",contaminate,structural=False))
    print(f"P5 mutation tests: {len(results)}/{len(results)} injected faults detected")
    for x in results: print(f"PASS {x['id']} via {x['detector']}: {x['evidence']}")
    return 0

if __name__=="__main__": raise SystemExit(main())
