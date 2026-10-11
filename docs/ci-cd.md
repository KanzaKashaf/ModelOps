# CI/CD Pipeline

## Jobs

| Job | Trigger | Purpose |
|-----|---------|---------|
| `changes` | Always | Detects which paths changed; gates downstream jobs |
| `quality` | code or docs | Ruff lint + fast unit tests |
| `data-and-model` | ML paths | Data validation, training smoke test, reload tests |
| `tracking-and-governance` | ML paths | MLflow tracking, promotion gate, champion promotion |
| `serving-api` | ML paths | API contract tests, OpenAPI schema validation |
| `model-contract` | ML paths | Schema alignment between training and serving |
| `security-scan` | code or config | Bandit (SAST), pip-audit (SCA), Gitleaks (secrets) |
| `test-report` | Always | Aggregates test results into a PR summary |

## Path-Based Gating

Heavy ML jobs are skipped when only documentation or configuration
changes. This keeps feedback fast for docs-only PRs while still
running the full pipeline for code changes.

| Filter | Paths | Gates |
|--------|-------|-------|
| `code` | `src/**`, `tests/**`, `pyproject.toml`, `requirements-dev.lock`, `.github/workflows/ci.yml` | `quality` |
| `ml` | `src/modelops/{data,training,evaluation,governance,serving}/**`, `tests/{api,contracts,integration}/**` | `data-and-model`, `tracking-and-governance`, `serving-api`, `model-contract` |
| `security` | `src/**`, `pyproject.toml`, `requirements-dev.lock`, `bandit.yaml`, `.gitleaks.toml`, `.github/workflows/ci.yml` | `security-scan` |
| `docs` | `**.md`, `docs/**` | (informational) |

## Security Tools

| Tool | Type | Fail threshold |
|------|------|----------------|
| Bandit | SAST | HIGH severity |
| pip-audit | SCA | Any CVE (unless explicitly ignored) |
| Gitleaks | Secrets | Any secret found |

### Bandit

Runs against `src/` only. Tests are excluded via `bandit.yaml`
because pytest uses `assert` extensively, which Bandit flags at LOW
severity. The `B101` rule (assert_used) is also skipped globally.

Configuration: `bandit.yaml` and `[tool.bandit]` in `pyproject.toml`.

### pip-audit

Audits `requirements-dev.lock`, not `pyproject.toml`, so the report
describes what will be deployed. The lockfile is regenerated via
`scripts/generate_lockfile.sh` whenever dependencies change.

Triaged CVEs with no fix available can be added to
`pip-audit-ignore.txt` with a dated comment explaining the
acceptance. This file does not currently exist because the lockfile
is CVE-free.

### Gitleaks

Scans the full Git history using the default ruleset, with a minimal
allowlist in `.gitleaks.toml` for MLflow artifacts and documentation
placeholders. Test fixtures are not allowlisted; if a fake secret
appears in a test, make it obviously fake (`not-a-real-key`) rather
than hiding the whole directory.

`GITLEAKS_LICENSE` is only required for organization accounts, not
personal ones.

## Model-Contract Checks

`tests/contracts/test_model_contract.py` verifies that the serving
schema (feature names, order, target name, feature count) matches
the training schema. This catches silent drift where a model is
retrained with different features but the API schema is not updated.

The contract is verified via:
- The Pandera `HousingSchema` for feature names and order.
- The `TARGET_COLUMN` constant for the target name.
- The JSON schema (client-facing contract) of `PredictRequest` for
  the feature count constraint.

## Trivy (Deferred to Phase 5)

Container scanning with Trivy is deferred to Phase 5, when a Docker
image exists.

**Security note:** Trivy's release pipeline was compromised in March
2026, and malicious images were published to Docker Hub. In Phase 5,
pin the Trivy GitHub Action by commit SHA, not by tag, and verify
image digests before scanning.

## Test Reports

Test results are uploaded as artifacts (`pytest-unit-report`,
`pytest-api-report`) and summarized in the PR's GitHub Step Summary.

The `quality` job runs all tests except API, contract, integration,
and reload tests. Those run in dedicated jobs (`serving-api`,
`model-contract`, `data-and-model`).

## Reproducing CI Locally

```bash
# Activate the venv
source .venv/bin/activate

# Lint
ruff check .

# Fast unit tests
pytest tests/ -v --ignore=tests/api --ignore=tests/contracts --ignore=tests/integration --ignore=tests/test_model_reload.py

# API contract tests
pytest tests/api -v

# Model-contract tests
pytest tests/contracts -v

# Security: Bandit
bandit -c bandit.yaml -r src/ -ll

# Security: pip-audit
./scripts/generate_lockfile.sh
pip-audit -r requirements-dev.lock --desc

# Security: Gitleaks
gitleaks detect --config .gitleaks.toml --redact