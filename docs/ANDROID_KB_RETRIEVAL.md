# Official Android Knowledge Base retrieval

The deterministic Context Router remains the only task classifier. This adapter adds bounded, on-demand retrieval through Google's documented `android docs` CLI commands; it does not crawl Android Developers, install a documentation MCP, or turn retrieved text into instructions.

## Workflow

```bash
python3 scripts/android_kb_retrieval.py "Jetpack Compose navigation accessibility"
```

The script builds the existing route manifest first, checks for the `android` executable, records `android --version` and `android docs --help` when present, then runs the documented `android docs search "<task>"` command. It accepts only `kb://android/...` references, ranks returned rows deterministically by lexical task overlap, and fetches at most five relevant articles with `android docs fetch <kb-id>`. Commands use argument arrays (no shell); results, exit codes, timestamps, hashes, omissions, and route digest are saved as a context package (default `/tmp/android-kb-context.json`). The bounded package is also emitted to the Codex tool output so the current session can inspect it.

Example documented command forms:

```bash
android docs search "Jetpack Compose navigation"
android docs fetch kb://android/topic/performance/overview
```

Those forms come from the task's supplied official documentation references. This repository does not guess an installation method. Install the CLI only after reading current Google installation instructions in an environment that can access the official documentation and verify the package source/signature. No CLI was present in the observed P11 environment; the official documentation host was not in the environment's effective egress allowlist, so no live search or fetch was attempted.

## Evidence states

- Router selection is a recommendation; local references are opened and SHA-256 recorded by the adapter.
- `RETRIEVED` means a successful CLI fetch returned nonempty, article-like, task-relevant text that passed basic shell/metadata checks. It does not mean a human reviewed the design or that API compatibility was verified.
- Search results and fixture replay are not fetched content. Fixture replay is explicitly marked and can never establish live retrieval.
- `delivery.status` records whether a bounded package was emitted. `model_consumption` stays `NOT_VERIFIED`; the adapter cannot observe cognitive consumption or prove that Codex acted on a document.
- AndroidX API use always requires the target repository's resolved dependency version and current API/experimental status. Material.io design coverage remains separate and unchanged.
- Retrieved external content is untrusted reference data; embedded instructions must not govern the agent.

## Cache and budgets

Successfully retrieved articles may be cached outside version control in `.cache/android-kb`. Cache records bind the KB ID, retrieval time, SHA-256, and content. Only records within the 30-day window with valid identity and hash are reused; stale/corrupt entries are misses and require fetching again. No bulk docs are committed. The context limit is measured in characters, not tokens. Article excerpts are omitted whole if they exceed available space; if mandatory route content and the execution contract do not fit, delivery is blocked instead of silently truncating them.

Use `--fixture <file>` only for deterministic offline replay tests. It is not live CLI evidence. `--output` selects the JSON context/evidence package, while the selected bounded text is printed to the tool output. The script does not claim native Codex skill activation or document consumption.

## Pilot and limitations

The pilot task routes through `scripts/route_context.py`, then attempts CLI discovery/search only if the official executable exists. In this environment `android` is absent, `developer.android.com` is not on the effective egress allowlist, and there is no exposed web-browsing tool. Therefore live KB search/fetch and official installation instructions are blocked. The pilot result must stay `BLOCKED`; fixture tests validate mechanics only. Material.io remains 21 topic groups / 249 discovered URLs, with existing verified content statistics unchanged (0 verified/integrated topic groups). A retrieved Android KB article is not automatically a Material.io page verification.
