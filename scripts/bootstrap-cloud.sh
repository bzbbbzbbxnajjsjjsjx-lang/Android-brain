#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# This repository is context infrastructure only; do not install Android tooling.
python3 scripts/validate_registry.py
python3 scripts/validate_skills.py
python3 scripts/validate_material_evidence.py
python3 evals/run_context_router_evals.py
python3 evals/run_skill_integration_evals.py
python3 evals/run_quality_gate_evals.py
python3 evals/run_harness_evals.py --output /tmp/android-harness-p5-routing-report.json
python3 evals/run_adversarial_evals.py
python3 evals/run_mutation_evals.py
