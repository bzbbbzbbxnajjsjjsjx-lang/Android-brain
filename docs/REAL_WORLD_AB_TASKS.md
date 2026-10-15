# Frozen task instructions for Android-brain A/B evaluation

Use each card verbatim in one fresh Codex session per arm. The initial task text must be byte-identical in A and B.

## Task 1 — Bookmark action semantics

```text
Add a focused Compose UI test for BookmarkButton accessibility in the existing core:ui module. Verify that the unbookmarked state exposes the localized Bookmark action and activating it invokes the callback; verify that the bookmarked state exposes the localized Unbookmark action and exposes checked state. Keep changes limited to the relevant test source unless a concrete production accessibility defect prevents the stated behavior. Inspect project instructions first, use existing dependencies and conventions, and run the most relevant build/test/static checks. Do not modify Gradle dependencies or unrelated files. Report exact commands, results, and any runtime checks that could not execute.
```

## Task 2 — Topic-tag announcements and action

```text
Add a focused Compose UI test for NewsResourceTopics accessibility in the existing core:ui module. Verify that followed and unfollowed topics expose the expected localized screen-reader descriptions and activating each topic invokes the callback with its topic ID. Keep changes limited to the relevant test source unless a concrete production accessibility defect prevents the stated behavior. Inspect project instructions first, use existing dependencies and conventions, and run the most relevant build/test/static checks. Do not modify Gradle dependencies or unrelated files. Report exact commands, results, and any runtime checks that could not execute.
```

## Task 3 — Bounded test-quality improvement

```text
Add a focused Compose UI test for NewsResourceCardExpanded's accessible card click action in the existing core:ui module. Verify that the localized card tap action label is exposed in click semantics and invoking the card activates onClick exactly once. Keep changes limited to the relevant test source unless a concrete production accessibility defect prevents the stated behavior. Inspect project instructions first, use existing dependencies and conventions, and run the most relevant build/test/static checks. Do not modify Gradle dependencies or unrelated files. Report exact commands, results, and any runtime checks that could not execute.
```

## Arm-specific setup (not part of the task text)

- **A / normal Codex:** a fresh NIA copy at the pinned SHA with its original `AGENTS.md` and no Android-brain files, router output, or prior trial context.
- **B / Android-brain:** a separate fresh copy at the same NIA SHA, integrated using the documented Android-brain installer. Follow its instruction to route first and inspect relevant selected context. This does not establish native skill invocation; capture actual file reads separately.

The project commit, model, reasoning effort, sandbox/tool availability, cache snapshot, test commands, and task text must match within each A/B pair. Do not share a patch or conversation between arms.
