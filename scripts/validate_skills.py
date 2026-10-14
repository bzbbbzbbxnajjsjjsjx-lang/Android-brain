#!/usr/bin/env python3
"""Check Codex skill metadata and the harness's local-reference contracts."""
import json
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_HEADINGS = (
    "Scope",
    "Preconditions and required context selection",
    "Applicable policy IDs",
    "Workflow",
    "Verification",
    "Failure and uncertainty",
)
POLICY_RE = re.compile(r"`([a-z][a-z0-9_]+)`")
KNOWLEDGE_RE = re.compile(r"(?<![\w./-])(knowledge/[\w./-]+\.md)")


def main() -> int:
    try:
        skills = json.loads((ROOT / "registry/skills.json").read_text())['skills']
        policies = {p['id'] for p in json.loads((ROOT / "registry/policies.json").read_text())['policies']}
        seen = set()
        local_count = 0
        for skill in skills:
            ident = skill['id']
            if ident in seen:
                raise ValueError(f"duplicate skill id: {ident}")
            seen.add(ident)
            path = (ROOT / skill['path']).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                raise ValueError(f"{ident}: missing or unsafe skill path {skill['path']}")
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---\n") or text.split("---\n", 2)[1].splitlines()[0] != f"name: {ident}":
                raise ValueError(f"{ident}: invalid Codex skill frontmatter/name")
            header = text.split("---\n", 2)[1]
            if not re.search(r"(?m)^description:\s*\S", header):
                raise ValueError(f"{ident}: missing activation description")
            for ref in KNOWLEDGE_RE.findall(text):
                if not (ROOT / ref).is_file():
                    raise ValueError(f"{ident}: broken knowledge reference {ref}")
            if skill['origin'] == 'local':
                local_count += 1
                missing = [h for h in REQUIRED_HEADINGS if f"## {h}" not in text]
                if missing:
                    raise ValueError(f"{ident}: missing skill sections {missing}")
                section = text.split("## Applicable policy IDs", 1)[1].split("\n## ", 1)[0]
                referenced = set(POLICY_RE.findall(section))
                if not referenced:
                    raise ValueError(f"{ident}: no explicit policy IDs")
                unknown = referenced - policies
                if unknown:
                    raise ValueError(f"{ident}: unknown policy IDs {sorted(unknown)}")
            elif skill['origin'] == 'google/android-skills':
                if not skill.get('source_revision') or not re.fullmatch(r"[0-9a-f]{40}", skill['source_revision']):
                    raise ValueError(f"{ident}: missing pinned Android Skills source revision")
                if skill.get('license') != 'Apache-2.0':
                    raise ValueError(f"{ident}: expected explicit Apache-2.0 license metadata")
                license_path = (ROOT / skill.get('license_path', '')).resolve()
                if not license_path.is_relative_to(ROOT) or not license_path.is_file():
                    raise ValueError(f"{ident}: missing adjacent upstream license")
                if 'Apache License' not in license_path.read_text(encoding='utf-8'):
                    raise ValueError(f"{ident}: license file does not identify Apache License")
                license_hash = hashlib.sha256(license_path.read_bytes()).hexdigest()
                if license_hash != skill.get('license_sha256'):
                    raise ValueError(f"{ident}: adjacent license hash differs from pinned registry hash")
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != skill.get('sha256'):
                    raise ValueError(f"{ident}: vendored skill hash differs from pinned registry hash")
        print(f"PASS: {len(skills)} registered Codex-compatible skill files; {local_count} custom skills have scoped activation, required sections, valid knowledge paths, and policy IDs.")
        return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
