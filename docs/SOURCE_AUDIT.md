# P0 source audit

All 17 supplied references have entries in `registry/sources.json`. `last_verified` is `2026-10-14` only for resources actually fetched or inspected that date; the Figma entries also record the date of the failed access check. Access status is per source and does not imply exhaustive site review.

## Retrieved or inspected

- OpenAI Codex workflow: raw Markdown.
- `android/skills`: clone, README, selected skill/reference files at commit `5bda39f154fb859a08d45e2392f3568e049f83fb`; isolated Android CLI install verified. Plugin commands were verified from upstream docs/CLI help, not installed globally.
- AndroidX MaterialShapes: official API HTML and AndroidX published artifact source/POM; Google Maven metadata queried for versions.
- Now in Android modularization: raw Markdown.
- Android Hilt and build variants: official developer pages.
- Now in Android screenshot path: GitHub contents API directory listing only.
- Roborazzi: README and Maven POM.
- Baseline Profile and Macrobenchmark: official Android developer pages.
- View-based Material Components motion: upstream raw Markdown.

## Partial or blocked

- Material Design 3 home, motion overview, and shape-principles URLs returned a JavaScript application shell. The design notes are explicitly conservative; they do not claim a full article extraction.
- All three supplied Figma URLs returned proxy HTTP 403. No Figma layer, asset, plugin interface, or token was inspected. The integration note specifies the evidence and export path needed when accessible.
- The NIA screenshot directory was listed but images were not copied or approved as references.

Retrieval may have cached source evidence under the shared workspace research directory during P0; those files are audit artifacts outside this repository and are not runtime dependencies. Re-fetch version-sensitive material when a future implementation task selects a target stack.

## Registry coverage

Each identifier maps to one independently retrievable note; fields in the registry include canonical URL, owner, type, authority, domain, task tags, retrieval method, skill/policy IDs, version sensitivity, verification date, access result, local note, and limitations.

| Source IDs | Classification / access |
|---|---|
| `codex_workflows` | OpenAI workflow example; raw Markdown retrieved |
| `google_android_skills` | Official Google skills repository; selected content and installation guidance retrieved |
| `material3_site`, `material_motion`, `material_shape_principles` | Official design guidance; page shell only |
| `material_shapes_api`, `androidx_material3_package`, `androidx_material_theme`, `androidx_motion_scheme`, `androidx_color_scheme`, `androidx_typography` | Official AndroidX API references; page bodies inspected; target-artifact verification remains required |
| `figma_theme_builder`, `figma_m3_kit`, `figma_nia_case_study` | Community-hosted design tools/references; proxy 403, no design contents accessed |
| `nia_modularization` | Official open-source Android architecture example; Markdown retrieved |
| `hilt_android`, `product_flavors`, `baseline_profiles`, `macrobenchmark` | Official Android implementation/performance guidance; pages retrieved |
| `nia_screenshots` | Official open-source screenshot directory; listing metadata only |
| `roborazzi` | Community testing tool; README/POM retrieved |
| `androidx_compose_adaptive`, `androidx_compose_accessibility` | Official Android Compose implementation guides fetched; verify current details at use time |
| `androidx_compose_material3_guide` | Official Android Developers Material 3 in Compose guide; article body retrieved and relevant implementation sections inspected on 2026-10-14; digest and sections are recorded separately in `routing/google-android-retrieval-evidence.json` |
| `legacy_view_motion` | Legacy View-system implementation documentation; Markdown retrieved |

## P2 Material sitemap discovery

On 2026-10-14, `https://m3.material.io/sitemap.xml` returned HTTP 200 (848,792 bytes; 3,567 URL entries). The harness saved 249 canonical `/foundations/`, `/styles/`, and `/components/` URLs to `routing/material3-sitemap-evidence.json`, excluding legacy `/v0/` and editorial paths. This exposed official topic areas for foundations and Expressive design, color, typography, layout/adaptivity, component anatomy/guidelines/specs/accessibility, interaction/state layers, tokens, navigation, spacing/density, elevation, icons, content, watches, and XR.

The sitemap is URL-discovery evidence, not page-text evidence. Material page bodies were not comprehensively reviewed; the root and sampled motion/shape pages previously returned JavaScript shells. `routing/material3-topics.json` labels each topic's access status, limitations, official URLs, related AndroidX implementation references, local notes, tasks, skills, policies, and required freshness actions. The official Android Developers implementation references for Compose accessibility, adaptive layouts, and Material 3 in Compose are separately attributed and must not be represented as inspected Material.io pages. Do not represent sitemap entries as extracted design rules.

P8 retrieved and inspected five official Android Developers/API response bodies (Material 3 in Compose, Compose accessibility, `MaterialTheme`, `ColorScheme`, and `Typography`) over HTTPS with TLS verification. Their extracted-text and response hashes, reviewed sections, and scope limitations are recorded in `routing/google-android-retrieval-evidence.json`. The summaries are implementation guidance only; current target-project artifact compatibility remains NOT VERIFIED until checked in that project.

P9 retrieved and inspected eleven Markdown documents directly from the official Google-maintained `material-components/material-components-android` repository at pinned revision [`60ff09436d5d477a4b9d02940f31eb01e1250620`](https://github.com/material-components/material-components-android/tree/60ff09436d5d477a4b9d02940f31eb01e1250620), using TLS-verified HTTPS to `raw.githubusercontent.com`. Body hashes, byte counts, inspected sections, revision, and upstream Apache-2.0 license evidence are in `routing/material-components-android-evidence.json`; concise original notes are under `knowledge/material3-view/`. This repository documents the legacy Android Views/XML library and its own README describes maintenance status. The notes are routed only for explicit View/XML or MDC-Android requests and must not be treated as Compose APIs or as evidence that any linked Material.io page was read. Material.io remains **21/21 groups and 249 URLs DISCOVERED; 0 page bodies retrieved; 0/21 groups VERIFIED**.

P10 adds a policy-gated Playwright retrieval/normalization pipeline and review-driven integration. The current environment has Playwright 1.62.0 and Chromium available for offline rendered-fixture tests, but its effective egress rules omit `m3.material.io` and the policy observation state is `unknown`; the five-page live pilot therefore made zero requests and recorded five BLOCKED attempts. `routing/material3-browser-retrieval-evidence.json` is separate from sitemap discovery and P8's Android Developers records. No Material.io page body was retrieved or integrated in P10. See `docs/MATERIAL3_INGESTION.md` for the supported owner-approved access and review workflow.

## P3 Codex Skills verification

On 2026-10-14, the selected Android Skills checkout was confirmed at commit `5bda39f154fb859a08d45e2392f3568e049f83fb`. The three vendored `SKILL.md` files (`testing-setup`, `jetpack-compose-performance`, `edge-to-edge`) are byte-identical to that checkout; each has adjacent Apache-2.0 license text matching the upstream repository `LICENSE.txt` SHA-256 `58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd`. The already installed Android CLI method and Codex plugin commands are recorded in `knowledge/android-skills/codex-integration.md`; no plugin was installed globally.

Codex CLI `0.159.2` `debug prompt-input` exposed the unique Material 3 skill activation description for a matching task. This verifies prompt-level metadata discoverability, not activation: the debug output did not include the selected skill body or show model invocation. The official `developers.openai.com/codex/skills` page was not re-fetched because `developers.openai.com` is absent from the managed environment's restricted HTTP allow-list. Therefore native skill invocation and current direct Codex documentation verification remain NOT VERIFIED.
