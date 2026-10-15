# First verified real Android engineering run

## Result

This case records one bounded Android engineering task supported by Android-brain and executed on a real Android emulator in GitHub Actions.

| Evidence | Result |
| --- | --- |
| Context routing | **VERIFIED** |
| Relevant skill and knowledge file reads in this evaluated session | **VERIFIED** |
| Android instrumentation execution | **VERIFIED** |
| Focused test result | **PASS** — one JUnit test case, no failure, error, or skip |
| Native Codex skill invocation | **NOT VERIFIED** |
| Independent A/B engineering-quality improvement | **NOT VERIFIED** |
| Live Material.io page content | **BLOCKED / NOT VERIFIED** |
| Live Android Knowledge Base retrieval | **BLOCKED / NOT VERIFIED** |

The run demonstrates a real test outcome with task-specific context. It does not establish that Android-brain improves results over normal Codex.

## Task and acceptance criteria

The task was to improve accessibility and stable test identification for the topic chips rendered by Now in Android's `NewsResourceTopics` and `NiaTopicTag`, without unnecessary architecture changes.

The focused Compose instrumentation test had to verify that followed and unfollowed topic chips expose their localized content descriptions and that activating each chip invokes the callback with that topic's ID. The test had to query the clickable chip through the normal merged semantics tree and execute on an Android emulator. Compilation alone was insufficient.

The application source was checked out at Now in Android commit [`a49ed253d75e61a2b6ab80a8da677b57437b08eb`](https://github.com/android/nowinandroid/commit/a49ed253d75e61a2b6ab80a8da677b57437b08eb). The evaluation was isolated to Android-brain branch `eval/nia-emulator-validation`; its successful harness commit is [`e53781ecc7b7434bc5ed16e517ab782c2a5f014b`](https://github.com/bzbbbzbbxnajjsjjsjx-lang/Android-brain/commit/e53781ecc7b7434bc5ed16e517ab782c2a5f014b). Android-brain `main` remained at `6b60bfcd74ab0653d3b867d1ad3607a365b0fd7b`. No changes were pushed to Google's repository.

## Context selected and read

The deterministic router was run for this task:

```bash
python3 scripts/route_context.py "Write an Android instrumented UI test for Compose semantics: localized accessibility descriptions and topic click callbacks in Now in Android core:ui." --as-of 2026-10-15 --project-config /tmp/nia-project-context.json
```

It classified `compose_ui` and `material3_accessibility`, and emitted a `routed_with_limitations` manifest. It recommended four local skills and three knowledge references, with an estimated selected-context size of 4,114 characters (within its 24,000-character budget). It also returned 11 policy summaries, including mandatory provenance, freshness, security, API, scope, and test-evidence constraints.

The evaluated manifest was retained outside the repository at `/tmp/nia-context-manifest-task.json`; its SHA-256 was `2c2019ba760464255491172350b9d1d72f932b40f13215e14e8c957d8b66259b`. The project context input was `/tmp/nia-project-context.json`. These temporary evaluation inputs are not committed.

The evaluated agent directly opened these four selected skill files:

- `android-testing` — SHA-256 `b5f9d21861611924dd8192a7565e5d21d0f3df1101f1c214feb47eefc8f37e40`
- `kotlin-compose` — SHA-256 `82f0870fcfdc4858569b0600aa93a10c72cdc26ea8cb76362793746623a84f59`
- `material3-expressive` — SHA-256 `1178b831333eeabe6c83fc9668cbe32dc96dc505c3429a7b41034b67d273a193`
- `visual-design-validation` — SHA-256 `db538feab15c0bca1dc15a109b012df764f12a839f16200b76f9aac606575dc8`

It directly opened these three selected knowledge files:

- `knowledge/androidx/compose-accessibility.md` — SHA-256 `6328703e89291401d8e4d4c70f71a2ab71c7f8ce22b62082e1b28b2a2e0acb27`
- `knowledge/material3/accessibility-interaction.md` — SHA-256 `fb83a3e32d4e20c57a19e3d8791a932de5618b7cd5c28a60964aa72d0da09ccd`
- `knowledge/material3/principles.md` — SHA-256 `e7adf8c3e18a16a9aeedfdd493e253323fc17168c28a7111adb4bccebde596de`

The AndroidX Compose accessibility reference was source-grounded in the official Android Developers guide and its retrieval record. The two Material 3 notes explicitly say their relevant Material.io page bodies were not verified. They were read as limitation and routing context; no Material.io design rule was claimed or used as verified evidence. The router did not perform live retrieval or compatibility checks.

These are distinct facts: the router **selected/recommended** skills; the evaluated agent **read** the listed `SKILL.md` and knowledge files; that does not prove that Codex's native skill mechanism **invoked** those skills. Native invocation is **NOT VERIFIED**. Reading files during the session is not evidence that the model automatically consumed every selected byte.

## Failure and correction

The first emulator workflow, [run 38756948679](https://github.com/bzbbbzbbxnajjsjjsjx-lang/Android-brain/actions/runs/38756948679) for evaluation commit `3a868e598819a5029e095e364dca1c873853b190`, used a test tag placed on the inner topic-label `Text`. The focused test could not find that tag in Compose's default merged semantics tree; the tag was visible only when querying the unmerged tree. This exposed a test-identity mismatch: the stable identifier belonged on the clickable topic-chip node that the test interacts with.

The correction moved the topic-specific test tag to the `NiaTopicTag`/`TextButton` root and passed its modifier directly to `TextButton` instead of an outer `Box`. The localized content description remained on the text and merged into the button semantics. The test now finds the button in the default merged tree, asserts the localized description, clicks it, and checks the callback's topic ID for followed and unfollowed fixtures. No new dependency or architecture layer was introduced.

The failed run's exact step and conclusion are available in GitHub metadata. Its downloadable logs were not accessible from this environment, so the detailed merged/unmerged diagnosis is recorded from the observed debugging and reproduction, not from a locally retrieved copy of that run's log.

## Validation evidence

Local checks on the pinned Now in Android checkout passed:

```text
:core:ui:compileDemoDebugAndroidTestKotlin
:core:ui:spotlessCheck
:core:ui:lintDemoDebug
BUILD SUCCESSFUL
```

The local command used the pinned checkout's wrapper with `--no-daemon`; `JAVA_HOME`, `ANDROID_HOME`/`ANDROID_SDK_ROOT`, `ANDROID_USER_HOME`, and `GRADLE_USER_HOME` pointed to the available JDK 21 and writable cached SDK/Gradle locations. Formatting and lint checks passed, and the Android test sources compiled.

These checks established compilation, formatting, and lint results; they did not establish device execution. The actual runtime result is from [GitHub Actions run 38761477327](https://github.com/bzbbbzbbxnajjsjjsjx-lang/Android-brain/actions/runs/38761477327), associated with Android-brain commit `e53781ecc7b7434bc5ed16e517ab782c2a5f014b`. Its API 34 job passed the focused instrumentation step, the JUnit XML gate, and artifact upload.

The exact test method was:

```text
com.google.samples.apps.nowinandroid.core.ui.NewsResourceCardTest
  #testTopicTagClick_exposesLocalizedDescriptionAndSendsTopicId
```

The hosted job ran `:core:ui:connectedDemoDebugAndroidTest` with the instrumentation class/method filter for this method, on API 34 with JDK 21 and the upstream emulator setup.

The workflow's JUnit verifier required exactly one matching testcase and rejected any `failure`, `error`, or `skipped` element. That check passed. Thus the focused method executed once as a JUnit case and **PASS**ed on the API 34 emulator; its assertions covered each followed/unfollowed fixture in that method.

The workflow uploaded [artifact `nia-api34-accessibility-instrumentation-e53781ecc7b7434bc5ed16e517ab782c2a5f014b`](https://github.com/bzbbbzbbxnajjsjjsjx-lang/Android-brain/actions/runs/38761477327/artifacts/11986257265) (artifact ID `11986257265`, 19,603 bytes; GitHub archive digest `sha256:658097079de95023381385bfd335b938d57e2dc301751c31254f472c439e85be`), containing connected test results, reports, and the focused Gradle log when present. GitHub's artifact metadata and successful upload step were observed. Downloading the archive from this environment was denied with HTTP 403 at GitHub's Azure-backed artifact host, so the XML file itself was not independently opened locally; the hosted workflow parsed and validated it before reporting success.

## What this case proves—and does not prove

- **Router selection** proves which context the deterministic router recommended for this task.
- **File reads** prove that this evaluated agent opened the listed local skill and knowledge files; they are recorded separately from selection.
- **Native skill invocation** means Codex's own skill mechanism activated/consumed a skill. No reliable invocation trace was available, so this remains **NOT VERIFIED**.
- **Instrumentation execution** is established by the successful API 34 emulator step and its passing JUnit XML gate, not by compilation.
- **Improvement over normal Codex** requires independent, equivalent A/B sessions and blind comparison. Those trials have not run; improvement remains **NOT VERIFIED**.

Material.io page-content verification remains **0/21 topic groups**; 21 topic groups and 249 discovered URLs are not page-content evidence. Live Android Knowledge Base access and native Codex skill invocation also remain unverified. This case is one reproducible engineering execution, not a comparative quality study or a stable-release claim.
