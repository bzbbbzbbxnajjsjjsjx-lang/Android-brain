# Material.io retrieval audit (P6)

The routing manifest still contains 21 Material Design 3 topic groups and covers all 249 URLs discovered in the official Material sitemap. URL discovery is not content retrieval or review.

On 2026-10-14, the public pages for [All buttons](https://m3.material.io/components/all-buttons) and [Color roles](https://m3.material.io/styles/color/roles) were fetched without authentication using `scripts/audit_material_page.py`. Both returned HTTP 200 and HTML with titles/descriptions. The non-script body text was only 31 characters and included “This website requires JavaScript”. Therefore the page-specific guidance itself was not retrieved. Response lengths, hashes, timestamps, and limitations are recorded in `routing/material3-retrieval-evidence.json`; response bodies were not retained.

A JavaScript-capable browser was also available during P7 (Playwright 1.62.0 and Chromium 154.0.8037.57). A Chromium navigation through the managed HTTP proxy to the official buttons page failed with `ERR_CERT_AUTHORITY_INVALID` while TLS verification remained enabled. The managed policy snapshot was restricted and did not list `m3.material.io` in its effective allowed hosts; its enforcement state was `unknown`. No TLS bypass or network-policy change was attempted. The failed attempt is recorded separately from HTTP page records and does not count as content retrieval.

Current states:

- **DISCOVERED:** 21/21 topic groups and 249/249 canonical sitemap URLs.
- **RETRIEVED shell:** 2 sampled URL responses; no page-body content.
- **CONTENT RETRIEVED:** 0 topic pages.
- **VERIFIED:** 0/21 topic groups.

`validate_material_evidence.py` keeps these states distinct. A `VERIFIED` record requires a successful content retrieval plus canonical URL, actual section, concise human-authored summary, review date, and reviewer. The structural validator does not authenticate the reviewer or prove that the summary is accurate; retain source/output evidence and conduct human source review. Do not create a design rule from titles or meta descriptions.

To repeat an allowed public retrieval, pass a URL already present in the recorded sitemap:

```bash
python3 scripts/audit_material_page.py \
  https://m3.material.io/components/all-buttons
```

The fetcher does not authenticate, bypass access controls, store page bodies, or mark content verified. If Material.io continues returning a JavaScript shell to supported retrieval methods, preserve the limitation and use an authorized design export only when one is provided.

## P8 source-family update

On 2026-10-14, the official Android Developers guide [Material Design 3 in Compose](https://developer.android.com/develop/ui/compose/designsystems/material3) and four related official Compose accessibility/AndroidX API reference pages returned substantive article text over HTTPS with TLS verification enabled. The guide's theming, color, typography, shape, elevation, components, navigation, customization, system UI, and accessibility sections were inspected; concise implementation notes are in `knowledge/androidx/compose-material3-system.md` and `knowledge/androidx/compose-accessibility.md`. Per-page hashes, extracted-text counts, access methods, and inspected sections are recorded in `routing/google-android-retrieval-evidence.json`.

These Android Developers and AndroidX records are a separate implementation-source family. They **do not** alter Material.io coverage: **21/21 topic groups and 249 URLs DISCOVERED; 2 sampled JavaScript shells; 0 Material.io page bodies CONTENT RETRIEVED; 0/21 topics VERIFIED**. The P8 execution environment exposed no supported rendered-browser tool. A direct fetch of the known Color roles URL again returned a JavaScript-required shell; prior recorded Chromium navigation failed TLS validation with verification enabled. Retrieval was stopped without disabling TLS or changing network policy. Material.io content coverage remains BLOCKED.

## P9 official Google repository references

P9 separately retrieved and inspected 11 official Markdown files from the Google-maintained Material Components for Android repository at revision `60ff09436d5d477a4b9d02940f31eb01e1250620`. These provide pinned **View/XML library** implementation notes for components, states, navigation, theming, motion, and shapes. Per-file hashes, byte counts, selected sections, and upstream Apache-2.0 license evidence are recorded in `routing/material-components-android-evidence.json`; original summaries are in `knowledge/material3-view/`. These are neither Material.io page content nor Jetpack Compose API contracts. The router excludes them from Compose tasks and selects them only after explicit View/XML/MDC-Android intent. This acquisition does not change Material.io's 0/21 verified page-content count.
