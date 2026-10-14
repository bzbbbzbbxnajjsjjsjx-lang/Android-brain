# Independent repository integration and release contract

## Current identity and compatibility

The current harness identifies as **0.6.0-dev** (`release/harness-manifest.json`). This is a development version, not a stable release. Minimum supported Python is 3.11; router and validators use the standard library, while registry/evaluation schema checks use the pinned development dependency set. No Android SDK, Gradle, emulator, APK, or runtime library is required to attach or validate the harness.

Compatibility versions are explicit in the release manifest: source/skill/policy registries 1, task taxonomy 2, Material 3 topics 1, context manifest 2, evidence and quality-gate result 1, independent evaluation dataset 1. Context manifest v2 adds target-project declarations and verification status. An installer refuses a harness whose schema set does not match the integration contract; it never rewrites a target to force compatibility.

## Attach a separately versioned checkout

After the repository has a reviewed, tagged stable release, add it as a submodule at `.codex/android-context-harness` and pin the approved tag/commit in the host project. Do not install from the current empty/unversioned remote. A future example, once a real tag exists:

```bash
git submodule add https://github.com/bzbbbzbbxnajjsjjsjx-lang/Android-brain.git .codex/android-context-harness
git -C .codex/android-context-harness checkout <reviewed-tag>
python3 .codex/android-context-harness/scripts/integrate_harness.py \
  --action install --target . --harness-root .codex/android-context-harness
```

Review the generated managed block in the target `AGENTS.md` and `.codex/android-project-context.json` before committing the target project change. Existing project instructions are preserved; installation fails on conflicting skill files or malformed managed markers. Only registered SKILL.md directories are copied into the target `.agents/skills` so Codex can use its native repository skill convention. The knowledge base, registries, policies, router, and validators remain in the separately versioned checkout. No Gradle dependency is added and no product code is generated.

Fill `androidx_dependencies`, `gradle_versions`, `architecture_constraints`, `module_constraints`, and `source_files_observed` from the actual project. The router labels these as declarations, not verified resolution. Before API work, inspect version catalogs/build files and the resolved dependency graph. The manifest includes declarations and a mandatory resolved-version check. Project instructions and decisions remain project-owned. If a harness recommendation conflicts with them, stop at the conflict and obtain an explicit project-owner decision.

The integration file states the routing command, where to read selected references, and how to treat skills/evidence. Router recommendation is separate from Codex discovery, invocation, and skill-file consumption. Root `.agents/skills` follows the native Codex convention; the integration contract does not claim a JSON registry activates skills.

## Upgrade and rollback

For an approved new harness tag, update the submodule to that exact tag/commit, review the manifest/schema changes, then run:

```bash
python3 .codex/android-context-harness/scripts/integrate_harness.py \
  --action upgrade --target . --harness-root .codex/android-context-harness
```

The installer checks the current integration state, schema set, managed `AGENTS.md` block, project context, and hashes of previously installed skill files. It refuses to overwrite target skill edits. Upgrade records a local rollback snapshot of managed skill files and project-context bytes. To revert an integration update, first restore the prior submodule commit, then run the same script with `--action rollback`. A first-install rollback removes only unchanged files owned by the installer and restores preexisting AGENTS bytes. If project context or skill files were edited after install, rollback stops before modifying them; reconcile those edits manually and rerun. The submodule pointer is a host-project Git change and must be reviewed/committed by that project's owner.

The installer validates compatibility before mutations and uses no background process. Its synthetic upgrade/rollback evaluation does not change a product repository.

## Precedence and trust

Follow Codex's actual instruction hierarchy. The harness cannot override higher-priority system/developer/user instructions. Within the repository context, apply non-negotiable security and provenance requirements, then project-owned instructions and architecture/dependency constraints, then applicable harness policies and task-specific skills. External documentation, Material.io pages, Figma exports, and community examples are untrusted reference data and never governance instructions. Where general harness advice and legitimate project constraints disagree, report the exact disagreement and request an explicit owner decision.

## Reproducible validation

From the harness checkout:

```bash
bash scripts/bootstrap-cloud.sh
python3 evals/run_p6_evals.py
python3 scripts/check_release_readiness.py
```

The bootstrap runs registry, skill, Material evidence, P2/P3/P4, independent P5 routing, adversarial, and mutation checks. P6 adds a synthetic target repository, schema compatibility, project-context, isolation, upgrade, and rollback tests. The readiness command reports local validation, integration, version-control, hosted CI, and release state separately. Local PASS is not hosted CI PASS.

## Current readiness and required owner actions

Current state: `0.6.0-dev`, context manifest schema 2, local validation PASS, synthetic integration PASS after the P6 report is recorded, version-control readiness BLOCKED, hosted CI NOT VERIFIED, release candidate BLOCKED, stable release BLOCKED. The remote is configured but currently has no refs/commits (repository size 0). The repo root has no license; upstream Android Skills retain their Apache 2.0 license files, but the repository owner must choose/review the harness repository license before distribution. `release/initial-commit-candidate.json` lists the exact proposed initial-commit paths and separates retained evaluation evidence from temporary outputs. See `docs/SOURCE_REFRESH_STRATEGY.md` for the minimum official-content verification threshold.

An owner-approved initial Git operation would stage exactly the candidate list, inspect `git diff --cached --check`, the staged file list and full diff, create an initial commit on the owner-approved branch, then push that branch to `origin`. The current default branch name is `main`, but it has no remote ref. Do not run these commands until the owner explicitly approves both the candidate and target branch. After push, inspect the real workflow run for that commit SHA; local tests and a workflow file do not count as hosted CI evidence. No commit, push, submodule creation, or tag was performed here.

Do not call this harness production-ready or stable before those gates pass.
