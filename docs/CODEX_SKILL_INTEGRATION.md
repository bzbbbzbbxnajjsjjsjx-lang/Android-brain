# Codex skill and context handoff

## Supported mechanisms and boundaries

Repository context enters through `AGENTS.md`; task skills are stored as `SKILL.md` files under `.agents/skills/<skill-name>/`. The router and JSON registries are repository-owned metadata: Codex does not automatically interpret them. A selected skill ID means **recommended**, not activated.

The selected official Android Skills are vendored unchanged at the Android Skills source revision recorded in `knowledge/android-skills/codex-integration.md`: `testing-setup`, `jetpack-compose-performance`, and `edge-to-edge`. Their exact source revision, SHA-256, Apache-2.0 license, and local license path are recorded per skill in `registry/skills.json`; the validator checks the local bytes and adjacent license. The remaining available Android skills are not copied indiscriminately. The upstream Android Skills README documents both `android skills add <skill> --agent=codex --project=.` and the Codex plugin marketplace flow (`codex plugin marketplace add android/skills`; `codex plugin add android-skills@android-skills`). The previously verified isolated Android CLI install populated `.agents/skills/`; no global plugin was installed for this task.

The installed Codex CLI is 0.159.2. Its local help exposes `codex plugin` operations, but no skill list/invoke command. `codex debug prompt-input` did expose the unique `material3-expressive` activation description for a matching task; `scripts/check_codex_skill_discovery.py` repeats that read-only metadata check using an isolated temporary `CODEX_HOME`. This is evidence of skill metadata discoverability by prompt assembly, not skill invocation or SKILL.md body consumption. The official Codex skills documentation at `https://developers.openai.com/codex/skills` could not be re-fetched in this managed environment because `developers.openai.com` is absent from the effective restricted network allow-list. Do not install a marketplace plugin globally just to imply activation.

## Task workflow

1. Run `python3 scripts/route_context.py "<task>" --as-of YYYY-MM-DD`.
2. Validate a saved JSON manifest with `python3 scripts/validate_context_manifest.py <manifest.json>`; the router itself checks selected skill and knowledge paths exist.
3. Inspect `classification`, `selected_skills`, `selected_knowledge_references`, `selected_policies`, `freshness`, `missing_or_inaccessible_context`, exclusions, and budget.
4. Let native Codex skill discovery operate from the project skill files. When the selected skill's presence or activation is not observable, explicitly read the recommended `SKILL.md` as task context. Read only selected knowledge notes. This is a fallback read, not proof that the native skill was invoked.
5. Recheck selected official sources and exact target dependency versions when required; no external fetch occurs in the router.
6. Report each state separately: repository skill file present, native metadata discovery observed/not observed, router recommendation, native invocation observed/not observed, `SKILL.md` read/not read, selected notes read/not read, and live freshness checked/not checked. Never promote “recommended” into “activated.”

## Skill selection and precedence

The router selects task-specific skills from its bounded taxonomy. `material3-expressive` is the primary skill for every Material 3 domain; `kotlin-compose` covers Compose UI implementation; `compose-architecture` covers Hilt, state ownership, modules, and build variants; `android-testing` and `visual-design-validation` split test execution from reference review; `android-performance` covers measurement while Google's Compose performance skill applies only to a relevant Compose bottleneck. The Context Engineering skill applies to harness tasks. These are routing conventions, not native skill priority metadata. Apply all selected skills when domains truly overlap, deduplicate common constraints, and exclude unrelated skills.

The comprehensive Material 3 taxonomy remains in `routing/material3-topics.json`: 21 topics and 249 official sitemap-discovered URLs. Material sitemap discovery does not establish page text was read. The Material skill resolves only topic references selected by the task; AndroidX source records remain separate implementation contracts. Figma remains an optional, access-dependent input.
