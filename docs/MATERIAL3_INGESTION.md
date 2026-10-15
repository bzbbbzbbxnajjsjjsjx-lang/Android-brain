# Material 3 official knowledge ingestion

The pipeline in `scripts/material3_knowledge_pipeline.py` acquires only canonical HTTPS URLs already present in `routing/material3-topics.json` and the recorded Material sitemap. It does not crawl arbitrary links, access credentials, bypass robots or TLS, install an agent/MCP, or collect the Material Components View/XML repository.

## States and storage

`DISCOVERED` comes from the existing 21-topic/249-URL sitemap manifest. A browser page with meaningful rendered documentation becomes `CONTENT_RETRIEVED`, with response and normalized-content fingerprints. A successful status or shell is insufficient. The normalized document cache is local under `.cache/material3-scraper/` and ignored by Git; it retains section heading paths, paragraphs, lists, tables, and allowlisted official documentation links. `routing/material3-browser-retrieval-evidence.json` stores retrieval metadata and hashes, not page bodies.

`VERIFIED` requires an editor-authored review JSON record matching the exact content fingerprint and source headings. It must supply an original summary, supported design rules, constraints, reviewed date and reviewer, freshness requirements, and routing terms. `integrate` generates a concise page note from that review and marks it `INTEGRATED`. The review fields are an attestation, not a cryptographic signature. Never copy full pages into notes. Material.io describes design intent; AndroidX APIs and target artifact compatibility must be checked separately.

The router validates the evidence on each route. It selects an integrated page note only when the task matches its Material topic and routing terms (or it is the sole integrated page in that topic). Unreviewed, stale-fingerprint, or blocked content never becomes context knowledge. Remaining URLs in a topic continue to be reported as unverified.

## Browser and access policy

The runtime requires Python Playwright and Chromium. Before opening a page, it checks the managed egress rules for `m3.material.io`; it requires current confirmation that policy is enforced, honors the site's `robots.txt` allow/disallow and crawl delay, visits pages sequentially, uses at least a two-second delay, retries at most twice, keeps TLS checks enabled, and refuses off-domain redirects. Third-party page requests are blocked; only the Material domain and limited Google-owned static asset hosts are allowed. Fingerprint-matched normalized documents are reused from the local cache. Refreshing an evidence file that already contains retrieved content is refused; use a separate `--evidence` output and re-review before replacing integrated knowledge.

In a managed cloud session, use `cloud_environment.environment_status` and proceed only when `observations_current` is true, the HTTP policy state is `enforced`, and the exact host is allowed. This repo's present environment reports policy state `unknown` and does not allow `m3.material.io`; therefore no live request was made. Do not edit the cloud allowlist from this repository or try another route around it. The repository owner must arrange approved egress/browser access, then run:

```sh
python3 scripts/material3_knowledge_pipeline.py pilot \
  --network-policy-enforced \
  --cache-dir .cache/material3-scraper \
  --evidence routing/material3-browser-retrieval-evidence.json
```

The pilot selects one registered URL for Foundations, Color, Typography, Components, and Accessibility. `--network-policy-enforced` is an operator attestation and never overrides a missing host rule. `--refresh` bypasses local cache only when writing to a new evidence file, so prior retrieval/review history cannot be silently replaced. Any blocked attempt remains explicit in evidence.

After examining a cached normalized document, write one review JSON per page in a private review directory. Required fields are `canonical_url`, `topic_id`, `content_fingerprint`, `reviewed_at`, `reviewer`, `summary`, `design_rules`, `constraints`, `source_sections`, `freshness_requirements`, and `routing_terms`. Then run:

```sh
python3 scripts/material3_knowledge_pipeline.py integrate \
  --evidence routing/material3-browser-retrieval-evidence.json \
  --cache-dir .cache/material3-scraper \
  --review-dir /path/to/review-records
```

Review data must use original concise wording and cite headings actually present in the extracted page. The generated note is checked against the captured URL and fingerprint. Tests use synthetic browser fixtures only and never assert that Material.io was fetched.

## Validation

Run `python3 scripts/validate_material3_browser_evidence.py` and `python3 evals/run_p10_material_scraper_evals.py`, followed by `bash scripts/bootstrap-cloud.sh` and the P6/P7 regression runners. Hosted CI installs the pinned Playwright version and Chromium for local fixture tests; CI does not crawl Material.io. Preserve the states `DISCOVERED`, `CONTENT_RETRIEVED`, `VERIFIED`, and `INTEGRATED` separately.
