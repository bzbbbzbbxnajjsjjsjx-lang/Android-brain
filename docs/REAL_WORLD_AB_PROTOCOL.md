# Real-world Android-brain A/B evaluation protocol

## Status

Protocol prepared; the independent comparative engineering trials have **not** run. The installed Codex CLI was callable, but its first independent `codex exec` could not reach the Codex Responses/MCP endpoints through the environment proxy (`HTTP CONNECT 403`). No model response or code change resulted from that attempt. A separate, single-arm accessibility task was later executed successfully on a GitHub Actions API 34 emulator; see [the real Android validation case study](REAL_ANDROID_VALIDATION.md). That run verifies only its focused instrumentation result and does not establish any comparative harness quality effect. A/B quality improvement remains **NOT VERIFIED**.

## Fixed project and model

- Project: Now in Android, source commit `a49ed253d75e61a2b6ab80a8da677b57437b08eb`.
- Harness: Android-brain baseline `f700ca6197dfad5da12546fc2767b44b534d041b`, plus the reviewed local context-package compaction under evaluation.
- Model configuration for all sessions: `gpt-6.1-sol`, reasoning effort `medium`, Codex CLI `0.159.2`, and identical `workspace-write` sandbox/tool permissions. This model is listed by the installed CLI; no session completed here.
- Live Material.io and Android Knowledge Base retrieval are unavailable/disabled for both arms. Neither arm may substitute inferred or mirrored documentation.
- Use six fresh project copies: three tasks × two arms. Every copy starts at the same NIA commit. Arm A receives only the project's own instructions; arm B receives the same project plus Android-brain installed by the documented integration script. Do not share conversation IDs, messages, patches, or test output between sessions. One Codex session per task per arm.
- Do not run sessions concurrently if that changes resource/cache conditions. Use the same model, reasoning, tool permissions, prompt, SDK/JDK, environment variables, and time budget for corresponding A/B sessions.

## Task cards

Use each task text exactly as written in `REAL_WORLD_AB_TASKS.md`. A and B must receive identical task text. The treatment is only whether the supported Android-brain integration is present.

For every B session, preserve observable records separately for: route command and manifest; recommended skill IDs; actual `SKILL.md` reads; local knowledge reads; policy reads; Android KB searches/fetches; source consumption; tool calls; and completion evidence. Recommendation is not invocation or reading. Do not infer any of those states from the manifest alone.

For every A session, record project instructions read and comparable tool/build/test activity. Do not provide Android-brain files, router output, or previous trial results to A.

## Isolation and cache controls

Create all six copies from one immutable, clean source snapshot at the pinned NIA commit. Keep repository and Gradle build outputs separate. Start corresponding A/B arms with byte-identical snapshots of the same Gradle dependency cache, or with empty caches for both. Never let one arm warm the other's cache. Run the same check order and capture elapsed times, cache state, exact commands, exit codes, and logs. Avoid using existing modified trial directories.

Use the same Android SDK/JDK and identical emulator/device image. Each task's required instrumented test must run on that same emulator/device class and API level in both arms. If no identical device is available, mark runtime comparison BLOCKED; compilation or fixture tests do not substitute for instrumentation.

## Acceptance and blind assessment

Before running agents, freeze the task-specific assertions and project-wide checks. Run the exact same checks on A and B. A reviewer who did not observe the sessions should assess anonymized implementation diffs, with integration-only files withheld from the code-quality view. Preserve a separate overhead record that includes integration files and harness work.

Record per task, per arm:

- Behavioral assertions and correctness defects.
- Compile, lint, unit-test, and instrumented-test outcomes (executed, failed, blocked, not run).
- AndroidX/API use against the pinned project's resolved dependencies; no compatibility claim without checking the actual project.
- Accessibility semantics and relevant manual assistive-technology review.
- Changed-file count, dependencies, architecture changes, unrelated edits, and maintainability findings.
- Codex model usage/token counts only if the session exposes actual usage. Otherwise record characters and tool calls separately; do not estimate tokens from characters.
- Context overhead: exact router JSON bytes/chars, selected knowledge chars, policy summary chars, skill file chars actually read, total agent input usage if observable, plus time/tool calls attributable to routing.
- Corrective iterations, defined as an agent change followed by a failed check and another corrective change.

The blind rubric scores each dimension on a pre-registered 0–2 ordinal scale: 0 = incorrect/unsafe, 1 = acceptable with material omissions, 2 = meets all task assertions. Do not collapse dimensions into an overall score until item-level results are reported. With three tasks this is descriptive evidence only, not a powered statistical claim. Report differences task-by-task and retain all failures.

Decision rule: Android-brain is shown to help only if B improves at least one predeclared correctness/API/accessibility dimension across tasks without regressing any mandatory check, and the blind reviewer can attribute the improvement to relevant context; report overhead alongside it. If outcomes tie, conclude “no measurable difference in this sample.” If B adds irrelevant context, defects, or extra iterations without a compensating verified improvement, report that it hurt. Do not claim general quality improvement from this small sample.

## Reproducibility and evidence

Save the immutable project SHA, harness SHA/worktree diff, task texts, model and CLI versions, configuration (excluding secrets), arm setup, device/build/cache details, manifests, session identifiers, exact commands, exit codes, logs, diffs, and blinded ratings. Redact secrets. Record unavailable evidence as BLOCKED or NOT VERIFIED. Do not commit or push trial changes to NIA.

## Current environment observation

Historical observation for the A/B attempt: the NIA source snapshot at the pinned commit was clean; Java 21 and Android SDK directories were present, but no local emulator executable/system image was found and `adb devices -l` listed no devices with a writable temporary `HOME`. The first Codex CLI session failed before model output because the configured proxy returned HTTP CONNECT 403 for `chatgpt.com/backend-api/codex/responses` and `/ps/mcp`. A later hosted emulator run is documented separately; it did not run independent A/B arms. No A/B result is claimed.
