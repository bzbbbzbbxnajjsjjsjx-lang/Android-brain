# Android Skills integration with Codex

The Android Skills repository documents two relevant paths: install the Android CLI then use its `android skills add ... --agent=codex` command, or install its Codex plugin using the documented Codex plugin marketplace/add commands. The Android CLI install was executed in an isolated project using Android CLI 1.0.16500706; it placed `testing-setup/SKILL.md` under `.agents/skills/`. Upstream README and Codex CLI help documented the plugin commands; the plugin itself was not globally installed.

This repository vendors only three unmodified upstream skills: `testing-setup`, `jetpack-compose-performance`, and `edge-to-edge`, with upstream license files. Their source revision is `5bda39f154fb859a08d45e2392f3568e049f83fb`. Local skills add source routing and project policy; when upstream advice assumes a library or framework, check project evidence and explicit task constraints before applying it. In particular, the upstream testing skill’s default Hilt/screenshot recommendations are not universal requirements.

To refresh: inspect upstream README, revision, skill changes, and license; select skills by task; review/update vendored files; rerun `python3 scripts/validate_registry.py`. Do not install all skills by default.

**Provenance:** `google_android_skills`; retrieved upstream README, selected `SKILL.md` files and references at the revision above; isolated install result recorded during P0 audit.
