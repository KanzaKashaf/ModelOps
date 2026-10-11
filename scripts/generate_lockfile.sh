#!/usr/bin/env bash
# Generate a requirements lockfile from pyproject.toml using uv.
# The lockfile pins the exact resolved dependency graph so that
# pip-audit audits what will be installed, not what happens to be
# present in a developer's environment.
set -euo pipefail
uv pip compile pyproject.toml --extra dev -o requirements-dev.lock
echo "Generated requirements-dev.lock"
