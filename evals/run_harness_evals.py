#!/usr/bin/env python3
"""Independent, task-level context quality evaluation (P5)."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DATA=ROOT/"evals/datasets/context_tasks.v1.json"
spec=importlib.util.spec_from_file_location("p5_router",ROOT/"scripts/route_context.py")
router=importlib.util.module_from_spec(spec); sys.modules[spec.name]=router; spec.loader.exec_module(router)
try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("BLOCKED: jsonschema is unavailable; install requirements-dev.txt",file=sys.stderr); raise SystemExit(2)

def read(p:Path): return json.loads(p.read_text(encoding="utf-8"))
def ids(manifest,key,field="id"): return {x[field] for x in manifest.get(key,[])}
def pct(n,d): return round(n/d,4) if d else 1.0

def evaluate_case(case:dict, global_policies:set[str], as_of:date, budget:int|None=None)->tuple[dict,dict]:
    m=router.build_manifest(case["task"],as_of=as_of,budget_chars=budget)
    required_domains=set(case["expected_domains"]); actual_domains=set(m["classification"]["matched_domains"])
    sources=ids(m,"selected_sources"); skills=ids(m,"selected_skills"); policies=ids(m,"selected_policies")
    knowledge=ids(m,"selected_knowledge_references","path")
    required_sources=set(case["required_sources"]); allowed_sources=required_sources|set(case["allowed_optional_sources"])
    required_skills=set(case["required_skills"]); allowed_skills=required_skills|set(case["allowed_optional_skills"])
    required_knowledge=set(case["required_knowledge"]); allowed_knowledge=required_knowledge|set(case["allowed_optional_knowledge"])
    required_policies=global_policies|set(case["required_policies"])
    fresh={x["source_id"]:x for x in m.get("freshness",{}).get("source_records",[])}
    source_status={x["id"]:x["accessibility_status"] for x in m["selected_sources"]}
    actions="\n".join(m.get("required_verification_actions",[])).casefold()
    failed=[]
    def assertion(condition,label):
        if not condition: failed.append(label)
    assertion(actual_domains==required_domains,f"domains expected={sorted(required_domains)} actual={sorted(actual_domains)}")
    expected_class_status=case.get("expected_classification_status")
    if expected_class_status: assertion(m["classification"]["status"]==expected_class_status,f"classification status expected={expected_class_status} actual={m['classification']['status']}")
    assertion(m["routing_status"]==case["expected_routing_status"],f"routing status expected={case['expected_routing_status']} actual={m['routing_status']}")
    missing_sources=required_sources-sources
    missing_skills=required_skills-skills
    missing_knowledge=required_knowledge-knowledge
    missing_policies=required_policies-policies
    forbidden=set(case["forbidden_sources"])&sources
    assertion(not missing_sources,f"missing required sources={sorted(missing_sources)}")
    assertion(not missing_skills,f"missing required skills={sorted(missing_skills)}")
    assertion(not missing_knowledge,f"missing required knowledge={sorted(missing_knowledge)}")
    assertion(not missing_policies,f"missing required policies={sorted(missing_policies)}")
    assertion(not forbidden,f"forbidden sources selected={sorted(forbidden)}")
    for sid in case["required_freshness_sources"]:
        assertion(sid in fresh,f"freshness record missing {sid}")
        if sid in fresh:
            assertion(fresh[sid]["live_verification_required"] is True,f"live freshness not required for {sid}")
            assertion(fresh[sid]["live_verification_performed"] is False,f"router pretended live freshness for {sid}")
    for sid, expected_access in case.get("expected_source_access", {}).items():
        assertion(source_status.get(sid)==expected_access,f"source {sid} access expected={expected_access} actual={source_status.get(sid)}")
        if expected_access in {"blocked_403","partial_js_shell","metadata_only"}:
            assertion(any(x.get("source_id")==sid and x.get("status")==expected_access for x in m["missing_or_inaccessible_context"]),f"inaccessible source {sid} limitation not surfaced")
    for term in case.get("required_evidence_actions",[]):
        assertion(term.casefold() in actions,f"required verification action missing phrase {term!r}")
    unknown=case["expected_routing_status"]=="uncertain_no_domain_match"
    ambiguous=case["expected_routing_status"]=="ambiguous_clarification_recommended"
    if unknown: assertion(not sources and not skills and not knowledge,"unknown task received domain context")
    if ambiguous: assertion(m["classification"]["status"]=="ambiguous","ambiguous task did not request clarification")
    m_topics=ids(m,"material3_topics")
    expected_topic_domains={d for d in required_domains if d.startswith("material3_") or d in {"material_motion","material_shapes"}}
    assertion(expected_topic_domains<=m_topics,f"Material topic route missing {sorted(expected_topic_domains-m_topics)}")
    budget_info=m["context_budget"]
    assertion(budget_info["estimated_selected_chars"]<=budget_info["limit_chars"] or budget_info["status"]=="mandatory_context_exceeds_limit","budget overflow was not explicit")
    first=json.dumps(m,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    second=json.dumps(router.build_manifest(case["task"],as_of=as_of,budget_chars=budget),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    deterministic=first==second
    assertion(deterministic,"same input did not produce identical manifest")
    result={"id":case["id"],"domain_group":case["domain_group"],"passed":not failed,"failures":failed,
      "classification":{"expected":sorted(required_domains),"actual":sorted(actual_domains),"exact_match":actual_domains==required_domains},
      "routing_status":{"expected":case["expected_routing_status"],"actual":m["routing_status"]},
      "sources":{"required":sorted(required_sources),"selected":sorted(sources),"missing":sorted(missing_sources),"forbidden_selected":sorted(forbidden),"precision":pct(len(sources&allowed_sources),len(sources)),"recall":pct(len(sources&required_sources),len(required_sources))},
      "skills":{"required":sorted(required_skills),"selected":sorted(skills),"missing":sorted(missing_skills),"precision":pct(len(skills&allowed_skills),len(skills)),"recall":pct(len(skills&required_skills),len(required_skills))},
      "knowledge":{"required":sorted(required_knowledge),"selected":sorted(knowledge),"missing":sorted(missing_knowledge),"precision":pct(len(knowledge&allowed_knowledge),len(knowledge)),"recall":pct(len(knowledge&required_knowledge),len(required_knowledge))},
      "policies":{"required":sorted(required_policies),"selected":sorted(policies),"missing":sorted(missing_policies),"coverage":pct(len(policies&required_policies),len(required_policies)),"duplicate_ids":len(m["selected_policies"])-len(policies)},
      "freshness":{"required_source_ids":case["required_freshness_sources"],"live_verification_claimed":m["freshness"]["live_checks_performed"],"status":m["freshness"]},
      "budget":{"unit":budget_info["unit"],"limit_chars":budget_info["limit_chars"],"estimated_chars":budget_info["estimated_selected_chars"],"status":budget_info["status"],"knowledge_refs":len(knowledge),"skill_instruction_chars_estimate":budget_info.get("potential_native_skill_instruction_chars")},
      "deterministic":deterministic}
    return result,m

def summarize(cases:list[dict])->dict:
    groups=defaultdict(list)
    for x in cases: groups[x["domain_group"]].append(x)
    per={}
    for domain,items in sorted(groups.items()):
        per[domain]={"cases":len(items),"classification_exact_accuracy":pct(sum(x["classification"]["exact_match"] for x in items),len(items)),
          "required_source_recall":round(sum(x["sources"]["recall"] for x in items)/len(items),4),"source_precision":round(sum(x["sources"]["precision"] for x in items)/len(items),4),
          "required_skill_recall":round(sum(x["skills"]["recall"] for x in items)/len(items),4),"skill_precision":round(sum(x["skills"]["precision"] for x in items)/len(items),4),
          "knowledge_recall":round(sum(x["knowledge"]["recall"] for x in items)/len(items),4),"knowledge_precision":round(sum(x["knowledge"]["precision"] for x in items)/len(items),4),
          "policy_coverage":round(sum(x["policies"]["coverage"] for x in items)/len(items),4),"forbidden_source_selections":sum(len(x["sources"]["forbidden_selected"]) for x in items),
          "cases_passed":sum(x["passed"] for x in items),"cases_failed":[x["id"] for x in items if not x["passed"]]}
    return per

def material_coverage(root:Path)->dict:
    topics=read(root/"routing/material3-topics.json")["topics"]
    sitemap_doc=read(root/"routing/material3-sitemap-evidence.json")
    urls=set(sitemap_doc["urls"])
    covered=set().union(*(set(t["canonical_source_urls"]) for t in topics))
    inspected=[t["id"] for t in topics if t["source_access_status"] in {"retrieved_page_content","page_content_verified"}]
    return {"topic_groups":len(topics),"expected_topic_groups":21,"known_urls":len(urls),"expected_known_urls":249,"categorized_urls":len(covered&urls),"uncategorized_urls":len(urls-covered),"verified_page_content_topics":len(inspected),"verified_page_content_topic_ids":inspected,"content_not_verified_topics":[t["id"] for t in topics if t["id"] not in inspected],"sitemap_is_not_page_content_evidence":True}

def run(data_path:Path=DEFAULT_DATA, output_path:Path|None=None)->int:
    data=read(data_path)
    if data.get("schema_version")!=1 or data.get("dataset_id")!="android-context-routing-independent-v1": raise ValueError("unsupported P5 dataset identity/version")
    dataset_schema=read(ROOT/"evals/schemas/context-task-dataset.schema.json")
    schema_errors=sorted(Draft202012Validator(dataset_schema).iter_errors(data),key=lambda e:list(map(str,e.path)))
    if schema_errors: raise ValueError("P5 dataset schema invalid: "+"; ".join(e.message for e in schema_errors[:8]))
    as_of=date.fromisoformat(data["evaluation_date"])
    global_policies=set(data["global_required_policies"])
    tasks=[]; manifests={}
    for case in data["tasks"]:
        result,m=evaluate_case(case,global_policies,as_of)
        tasks.append(result);manifests[case["id"]]=m
    per_domain=summarize(tasks)
    material=material_coverage(ROOT)
    aggregate={"task_count":len(tasks),"task_pass_count":sum(t["passed"] for t in tasks),"classification_exact_accuracy":pct(sum(t["classification"]["exact_match"] for t in tasks),len(tasks)),
      "required_source_recall":round(sum(t["sources"]["recall"] for t in tasks)/len(tasks),4),"source_precision":round(sum(t["sources"]["precision"] for t in tasks)/len(tasks),4),
      "required_skill_recall":round(sum(t["skills"]["recall"] for t in tasks)/len(tasks),4),"skill_precision":round(sum(t["skills"]["precision"] for t in tasks)/len(tasks),4),
      "knowledge_recall":round(sum(t["knowledge"]["recall"] for t in tasks)/len(tasks),4),"knowledge_precision":round(sum(t["knowledge"]["precision"] for t in tasks)/len(tasks),4),
      "policy_coverage":round(sum(t["policies"]["coverage"] for t in tasks)/len(tasks),4),"forbidden_source_selections":sum(len(t["sources"]["forbidden_selected"]) for t in tasks),
      "deterministic_cases":sum(t["deterministic"] for t in tasks),"budget_estimated_chars":{"mean":round(sum(t["budget"]["estimated_chars"] for t in tasks)/len(tasks),2),"max":max(t["budget"]["estimated_chars"] for t in tasks),"unit":"characters"}}
    # Set before execution and never adjust based on measured results.
    thresholds={"classification_exact_accuracy":0.90,"required_source_recall":0.95,"source_precision":0.80,"required_skill_recall":0.90,"skill_precision":0.80,"knowledge_recall":0.90,"knowledge_precision":0.75,"policy_coverage":1.0,"forbidden_source_selections":0,"deterministic_cases":len(tasks)}
    threshold_failures=[]
    for key,threshold in thresholds.items():
        actual=aggregate[key]
        if key=="forbidden_source_selections": ok=actual<=threshold
        elif key=="deterministic_cases": ok=actual==threshold
        else: ok=actual>=threshold
        if not ok:
            comparator = "==" if key in {"forbidden_source_selections", "deterministic_cases"} else ">="
            threshold_failures.append({"metric":key,"expected":f"{comparator}{threshold}","actual":actual})
    cov=material
    if cov["topic_groups"]!=21 or cov["known_urls"]!=249 or cov["categorized_urls"]!=249 or cov["uncategorized_urls"]!=0:
        threshold_failures.append({"metric":"material_url_coverage","expected":"21 topics and all 249 URLs categorized","actual":cov})
    report={"schema_version":1,"dataset_id":data["dataset_id"],"evaluation_date":data["evaluation_date"],"methodology":data["methodology"],"thresholds_fixed_before_run":thresholds,"aggregate":aggregate,"per_domain":per_domain,"material_coverage":material,"tasks":tasks,"threshold_failures":threshold_failures,"overall_status":"PASS" if not threshold_failures and all(t["passed"] for t in tasks) else "FAIL","budget_estimator_limitations":"The router measures estimated selected knowledge/policy characters, not model tokens. Native skill instruction sizes are separate estimates and are not activated by the router."}
    result_schema=read(ROOT/"evals/schemas/p5-evaluation-result.schema.json")
    result_errors=sorted(Draft202012Validator(result_schema,format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(report),key=lambda e:list(map(str,e.path)))
    if result_errors: raise ValueError("P5 result schema invalid: "+"; ".join(e.message for e in result_errors[:8]))
    text=json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text+"\n",encoding="utf-8")
    print(f"P5 independent dataset: {len(tasks)} tasks; task-level PASS {aggregate['task_pass_count']}/{len(tasks)}; status {report['overall_status']}")
    print("Metrics:",json.dumps(aggregate,sort_keys=True))
    for domain,summary in per_domain.items(): print(f"DOMAIN {domain}: {json.dumps(summary,sort_keys=True)}")
    for task in tasks:
        if not task["passed"]: print(f"FAIL {task['id']}: {'; '.join(task['failures'])}")
    print("Material coverage:",json.dumps(material,sort_keys=True))
    if threshold_failures: print("FAIL thresholds:",json.dumps(threshold_failures,sort_keys=True))
    if output_path: print(f"Report written: {output_path}")
    return 0 if report["overall_status"]=="PASS" else 1

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--dataset",type=Path,default=DEFAULT_DATA);parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    try: raise SystemExit(run(args.dataset,args.output))
    except (AssertionError,KeyError,OSError,ValueError) as exc: print(f"FAIL: {exc}",file=sys.stderr);raise SystemExit(1)
