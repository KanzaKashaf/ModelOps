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


## Serving API

Start the API (requires the local champion artifact or a running
MLflow server):

```bash
python -m modelops.serving


```markdown
# ModelOps Platform

[![CI](https://github.com/KanzaKashaf/ModelOps/actions/workflows/ci.yml/badge.svg)](https://github.com/KanzaKashaf/ModelOps/actions/workflows/ci.yml)

A production-style MLOps platform...


## CI/CD

Continuous integration runs on GitHub Actions. See
[docs/ci-cd.md](docs/ci-cd.md) for the job inventory, path-based
gating rules, security tooling, and the model-contract contract.

The pipeline includes:
- Ruff linting and pytest unit tests
- Data validation, training smoke test, and model reload tests
- MLflow tracking, promotion gate, and champion promotion
- Serving API contract tests and OpenAPI schema validation
- Model-contract tests (schema alignment between training and serving)
- Security scanning: Bandit (SAST), pip-audit (SCA), Gitleaks (secrets)
- Test report aggregation into the PR summary


```markdown
## Infrastructure as Code

The local Docker resources are also declarative via Terraform in
`infra/local-docker/`. This is a learning exercise that demonstrates
providers, resources, variables, outputs, state, and dependency
graphs — on a zero-cost, local target.

```bash
cd infra/local-docker
terraform init
terraform plan -var="image_tag=$(git rev-parse --short HEAD)" -var="model_path=$(pwd)/../../models"


```markdown
## Kubernetes

The serving API is deployed to a local kind cluster with a Deployment, ClusterIP Service, ConfigMap, Secret, and PersistentVolumeClaim.

```bash
# Create the cluster
kind create cluster --config k8s/kind-config.yaml

# Apply the manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pv-model.yaml
kubectl apply -f k8s/pvc-model.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Port-forward and test
kubectl port-forward -n modelops svc/modelops-serving 8081:80
curl http://127.0.0.1:8081/health/ready



```markdown
## GitOps

The serving chart is reconciled by Argo CD from
`gitops/argocd-app.yaml`. See [docs/gitops.md](docs/gitops.md)
for sync policy, drift correction, and rollback procedures.

```bash
# Port-forward Argo CD UI
kubectl port-forward svc/argocd-server -n argocd 8090:443

# Port-forward serving API
kubectl port-forward -n modelops svc/modelops-serving 8081:80