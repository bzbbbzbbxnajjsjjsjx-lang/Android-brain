#!/usr/bin/env python3
"""Observe whether Codex exposes this project's skill metadata to prompt assembly.

This is a read-only local CLI diagnostic. It does not invoke an LLM or prove
that any skill instructions were activated/read by a model.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "Implement a Material 3 color system in Jetpack Compose."
SKILL_ID = "material3-expressive"


def description(skill_path: Path) -> str:
    text = skill_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md has no frontmatter")
    header = text.split("---\n", 2)[1]
    for line in header.splitlines():
        if line.startswith("description:"):
            return line.partition(":")[2].strip().strip("\"'")
    raise ValueError("SKILL.md has no activation description")


def main() -> int:
    binary = os.environ.get("CODEX_BINARY") or shutil.which("codex") or "/opt/codex/bin/codex"
    if not Path(binary).is_file():
        print("BLOCKED: Codex CLI is unavailable; repository skill files were not observed by a Codex loader.")
        return 2
    skill_file = ROOT / ".agents/skills" / SKILL_ID / "SKILL.md"
    try:
        expected = description(skill_file)
        with tempfile.TemporaryDirectory(prefix="codex-skill-probe-") as home:
            env = os.environ.copy()
            env["CODEX_HOME"] = home
            proc = subprocess.run(
                [binary, "-C", str(ROOT), "debug", "prompt-input", TASK],
                env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30, check=False,
            )
        if proc.returncode:
            print(f"BLOCKED: Codex debug prompt-input exited {proc.returncode}; no discovery result.")
            return 2
        prompt_inputs = json.loads(proc.stdout)
        visible = json.dumps(prompt_inputs, ensure_ascii=False)
        if expected not in visible:
            print("FAIL: Codex prompt-input did not expose the selected skill's unique activation description.")
            print("NOT VERIFIED: native skill invocation/reading was not observed.")
            return 1
        print(f"PASS: Codex prompt-input exposed the {SKILL_ID} activation description for a matching task.")
        print("NOT VERIFIED: prompt metadata visibility does not establish that a model invoked or read SKILL.md.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"BLOCKED: {type(exc).__name__}: Codex skill discovery could not be observed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
