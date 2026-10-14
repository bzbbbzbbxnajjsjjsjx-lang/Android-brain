#!/usr/bin/env python3
"""P3 routing-to-skill integration evaluations; no Android project required."""
from __future__ import annotations
import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("route_context", ROOT / "scripts/route_context.py")
router = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = router
spec.loader.exec_module(router)
AS_OF = date(2026, 10, 14)
try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("BLOCKED: install requirements-dev.txt for JSON Schema evaluations", file=sys.stderr)
    raise SystemExit(2)
SCHEMA = json.loads((ROOT / "routing/context-manifest.schema.json").read_text())


def route(task: str) -> dict:
    result = router.build_manifest(task, as_of=AS_OF)
    Draft202012Validator(SCHEMA).validate(result)
    return result


def src(m): return {x['id'] for x in m['selected_sources']}
def skl(m): return {x['id'] for x in m['selected_skills']}
def know(m): return {x['path'] for x in m['selected_knowledge_references']}
def pol(m): return {x['id'] for x in m['selected_policies']}
def topics(m): return {x['id'] for x in m['material3_topics']}
def need(ok, message):
    if not ok: raise AssertionError(message)


def run():
    cases=[]
    # A: Material 3 Color.
    a=route("Implement a Material 3 color system in Jetpack Compose.")
    need('material3-expressive' in skl(a), "A missing unified Material 3 skill")
    need({'material3_site','androidx_color_scheme','androidx_material_theme'} <= src(a), "A missing design/API color references")
    need('knowledge/material3/color-typography.md' in know(a), "A missing color/typography knowledge")
    need(not ({'android-performance','jetpack-compose-performance'} & skl(a)), "A selected unrelated performance skill")
    cases.append(("A Material 3 Color",a))
    # B: Typography and accessibility.
    b=route("Review typography hierarchy and accessibility in Material 3.")
    need({'material3_typography','material3_accessibility'} <= topics(b), "B missing typography/accessibility topics")
    need({'accessibility_review','design_compliance'} <= pol(b), "B missing accessibility/design policy")
    need('knowledge/material3/color-typography.md' in know(b), "B missing typography knowledge")
    need('hilt_android' not in src(b), "B selected unrelated Hilt source")
    cases.append(("B Material 3 Typography",b))
    # C: Components, not motion/shape-only routing.
    c=route("Implement Material 3 Expressive components.")
    need({'material3_components','material3_expressive'} <= topics(c), "C did not route Material component domain")
    need({'material3_site','androidx_material3_package'} <= src(c), "C missing Material design/API sources")
    need('material3-expressive' in skl(c), "C missing complete Material 3 skill")
    need('knowledge/material3/components-states.md' in know(c), "C missing component knowledge")
    need(not ({'hilt_android','figma_m3_kit','macrobenchmark','baseline_profiles'} & src(c)), "C loaded unrelated architecture/Figma/performance context")
    cases.append(("C Material 3 Components",c))
    # D: MotionScheme API mapping and version verification.
    d=route("Use MotionScheme in Jetpack Compose.")
    need({'material_motion','androidx_motion_scheme'} <= src(d), "D missing Material/AndroidX motion sources")
    need({'api_compatibility','no_hallucinated_api'} <= pol(d), "D missing version/API verification")
    need('material3-expressive' in skl(d), "D missing Material 3 skill")
    need(not ({'hilt_android','macrobenchmark','baseline_profiles'} & src(d)), "D loaded unrelated architecture/performance context")
    cases.append(("D MotionScheme",d))
    # E: MaterialShapes and experimental status.
    e=route("Use MaterialShapes with shape morphing.")
    need({'material_shape_principles','material_shapes_api'} <= src(e), "E missing shape design/API references")
    need({'experimental_api','api_compatibility'} <= pol(e), "E missing experimental/dependency checks")
    need('material3-expressive' in skl(e), "E missing comprehensive Material skill")
    need(not ({'hilt_android','macrobenchmark','baseline_profiles'} & src(e)), "E loaded unrelated Hilt/performance context")
    cases.append(("E MaterialShapes",e))
    # F: Hilt without visual context.
    f=route("Review Hilt dependency injection.")
    need('hilt_android' in src(f), "F missing official Hilt source")
    need('compose-architecture' in skl(f), "F missing Compose architecture skill")
    need({'architecture_boundaries','dependency_selection'} <= pol(f), "F missing architecture/dependency policy")
    need(not (topics(f) or {'material3_site','material_motion','figma_m3_kit'} & src(f)), "F loaded unrelated Material/Figma context")
    cases.append(("F Hilt",f))
    # G: Screenshot tests and approved baseline policy.
    g=route("Implement a Roborazzi screenshot testing strategy.")
    need({'roborazzi','nia_screenshots'} <= src(g), "G missing screenshot references")
    need({'android-testing','visual-design-validation'} <= skl(g), "G missing testing/visual skills")
    need({'visual_baseline_approval','testing_evidence'} <= pol(g), "G missing baseline/evidence policies")
    need(not ({'figma_theme_builder','figma_m3_kit','figma_nia_case_study'} & src(g)), "G loaded optional Figma context")
    cases.append(("G Screenshot Testing",g))
    # H: Measurement-based startup performance only.
    h=route("Plan startup performance optimization.")
    need({'macrobenchmark','baseline_profiles'} <= src(h), "H missing performance references")
    need('android-performance' in skl(h) and 'measurement_first' in pol(h), "H missing measurement-first skill/policy")
    need(not any(term in json.dumps(h).lower() for term in ['measured improvement: true','performance improved']), "H asserted a measured performance gain")
    need(not ({'material3_site','material_motion','material_shape_principles','figma_m3_kit'} & src(h)), "H loaded unrelated Material/Figma context")
    cases.append(("H Performance",h))
    # I: Figma access is blocked, with no fabricated tokens.
    i=route("Extract color tokens from an inaccessible Figma Design Kit.")
    need('figma_m3_kit' in src(i), "I missing correct Figma reference")
    need(any(x.get('source_id')=='figma_m3_kit' and x.get('status')=='blocked_403' for x in i['missing_or_inaccessible_context']), "I omitted Figma access limit")
    need(any('export' in x.get('required_action','').lower() for x in i['missing_or_inaccessible_context']), "I missing authorized export action")
    need(any('no exact token values' in x.get('detail','').lower() for x in i['missing_or_inaccessible_context']), "I omitted no-token evidence")
    cases.append(("I Inaccessible Figma",i))
    # J: harness only.
    j=route("Improve the Context Router's skill selection.")
    need(j['classification']['matched_domains']==['harness_only'], "J did not isolate harness task")
    need('android-engineering' in skl(j), "J missing Context Engineering skill")
    need(not ({'compose_ui','material3_expressive','material_motion','performance'} & set(j['classification']['matched_domains'])), "J selected app implementation route")
    need(not ({'material3_site','hilt_android','macrobenchmark','androidx_material3_package'} & src(j)), "J loaded app implementation sources")
    cases.append(("J Harness-Only",j))
    # K: multiple domains, unique policy/skill/source IDs and bounded context.
    k=route("Review Material 3 Expressive accessibility and screenshot validation.")
    need({'material3_accessibility','material3_expressive','screenshot_testing'} <= set(k['classification']['matched_domains']), "K missed Material and visual domains")
    need({'material3-expressive','visual-design-validation','android-testing'} <= skl(k), "K missing combined task skills")
    for key, field in [('selected_sources','id'),('selected_skills','id'),('selected_policies','id'),('selected_knowledge_references','path')]:
        values=[x[field] for x in k[key]]
        need(len(values)==len(set(values)),f"K duplicates {key}")
    need(k['context_budget']['status'] in {'within_budget','mandatory_context_exceeds_limit'},"K missing budget accounting")
    need(k['context_budget']['estimated_selected_chars'] <= k['context_budget']['limit_chars'],"K exceeded its configured budget unexpectedly")
    cases.append(("K Multi-Domain",k))
    # L: repository discovery candidates are observable; native activation is not.
    skills=json.loads((ROOT/'registry/skills.json').read_text())['skills']
    for skill in skills:
        path=ROOT/skill['path']
        need(path.is_file(),f"L missing skill file {skill['id']}")
    l=route("Use a verified Material 3 color token in Compose.")
    evidence=l['skill_execution_evidence']
    need(evidence['codex_native_discovery']=='not_observed_by_router',"L overclaims native discovery")
    need(evidence['skill_invocation']=='not_observed' and evidence['skill_md_read_by_session']=='not_observed',"L overclaims skill use")
    need(evidence['recommended_skill_ids']==sorted(skl(l)),"L recommendation evidence mismatch")
    probe = subprocess.run([sys.executable, str(ROOT/'scripts/check_codex_skill_discovery.py')], text=True, capture_output=True, timeout=40)
    if probe.returncode == 0:
        print(probe.stdout.strip())
    elif probe.returncode == 2:
        print("NOT VERIFIED: L native Codex skill discovery could not be observed in this environment.")
    else:
        raise AssertionError("L Codex prompt-input did not expose the selected skill description")
    print("NOT VERIFIED: L native skill invocation or SKILL.md consumption is not exposed by prompt-input; no LLM session was simulated.")
    for name,m in cases:
        need(all(s['activation']=='recommended_not_activated' for s in m['selected_skills']),f"{name} overclaims skill invocation")
        need(m['skill_execution_evidence']['external_freshness_verified'] is False,f"{name} overclaims live freshness")
        print(f"PASS: {name}: {m['routing_status']} ({len(m['selected_skills'])} skills, {len(m['selected_sources'])} sources)")
    repeat=route("Implement a Material 3 color system in Jetpack Compose.")
    need(json.dumps(cases[0][1],sort_keys=True)==json.dumps(repeat,sort_keys=True), "P3 route output is nondeterministic")
    print("PASS: repeated P3 task produced an identical route manifest.")
    invalid=dict(cases[0][1])
    invalid.pop('skill_execution_evidence')
    need(bool(list(Draft202012Validator(SCHEMA).iter_errors(invalid))), "manifest schema accepted missing skill evidence")
    print("PASS: context manifest schema rejects missing skill-execution evidence.")
    print(f"PASS: {len(cases)} task scenarios; all manifests validated against Draft 2020-12 schema.")
    print("PASS: skill recommendation is distinct from native discovery, invocation, file reads, and external freshness.")


if __name__=='__main__':
    try: run()
    except (AssertionError,KeyError,OSError,ValueError) as exc:
        print(f"FAIL: {exc}",file=sys.stderr); raise SystemExit(1)
