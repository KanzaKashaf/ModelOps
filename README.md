# ModelOps Platform

A production-style MLOps platform demonstrating the complete ML and DevOps lifecycle.

## Setup

See [docs/windows-setup.md](docs/windows-setup.md) for Windows setup instructions.

## Local Linting Note (Windows)

If `ruff check .` is blocked by a WDAC (Windows Defender Application Control) policy with error 4551, local linting is unavailable. Use the CI workflow instead—Ruff runs on `ubuntu-latest` where no such policy exists. Run `pytest` locally and rely on the PR check for linting.

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Branch Strategy

- `main` — protected branch, always deployable.
- Feature branches: `feature/<short-description>`
- Pull requests require passing CI before merge.



## Model Governance

Model promotion is gated by deterministic quality criteria. See
[docs/model-governance.md](docs/model-governance.md) for the policy,
workflow, and rollback procedure.

Quick start:

```powershell
# Start MLflow (separate terminal)
.\scripts\start_mlflow.ps1

# Train and register candidates
python -m modelops.training.train_mlflow

# Evaluate promotion (dry-run)
python scripts/promote_model.py manifests/gradient_boosting-v9.json --dry-run

# Promote if approved
python scripts/promote_model.py manifests/gradient_boosting-v9.json