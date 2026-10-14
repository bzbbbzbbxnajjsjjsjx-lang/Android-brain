# Source refresh strategy

`routing/source-refresh-policy.json` contains one refresh record for every
source currently in `registry/sources.json`. It copies each source's recorded
verification date, access status, sensitivity, retrieval method, related skills,
and policies, then states a task-appropriate refresh trigger and failure path.
The copied date is registry provenance; it does not mean this P7 run rechecked
that source.

Refresh only sources selected for a task. For version-sensitive AndroidX work,
inspect the target repository's version catalog/build files and resolved
dependency graph, then check the official API/release documentation for that
version. Material.io supplies design intent; AndroidX references supply actual
Compose APIs. A Material.io illustration never establishes a Kotlin signature.
Figma remains optional and requires an authorized export or view link.

Allowed methods are those recorded per source: official published pages/API
references, public repository documentation/revisions, or authorized Figma
exports. Do not bypass login, access controls, TLS validation, or the managed
network allowlist. Record a failure as blocked or unverified, preserve the
cached reference with its provenance, and do not turn a failed refresh into a
claim that the content is current. A JavaScript shell, HTTP 200 status, title,
description, or sitemap entry is not page-content retrieval.

## Minimum source-verification policy for release

For stable release, every integrated Material design claim must be traceable to
an official Material.io page whose body was actually retrieved and reviewed.
Require at least one `VERIFIED` page in each priority family: foundations,
color, typography, components, and accessibility. Any additional topic with no
verified page remains explicitly unavailable for page-specific claims; it may
not be summarized from its URL/title. AndroidX implementation advice separately
requires official API provenance and target-project compatibility checks. This
policy does not require retrieving every sitemap URL, but it prohibits claiming
full Material content coverage from URL discovery alone.

Current P7 observation: 21 topics and 249 sitemap URLs are discovered; two
JavaScript shells returned HTTP 200, zero page bodies were retrieved, and zero
topics are content-verified. The managed environment's restricted egress list
does not include `m3.material.io`; Chromium/Playwright is installed, but the
attempted official page navigation failed certificate validation with TLS
verification enabled. No browser or TLS bypass was used. Material knowledge
verification therefore remains blocked and the minimum stable-release source
policy is not met.
