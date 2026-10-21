# ModelOps Platform

[![CI](https://github.com/KanzaKashaf/ModelOps/actions/workflows/ci.yml/badge.svg)](https://github.com/KanzaKashaf/ModelOps/actions/workflows/ci.yml)

A production-style MLOps platform demonstrating the complete machine learning and DevOps lifecycle: data validation, reproducible training, experiment tracking, model governance, API serving, CI/CD, containerisation, observability, drift monitoring, incident response, and retraining.

**Local-first.** No paid cloud services are required. The supported local runtime uses Docker Compose.

## Architecture

```text
Developer Workflow
Git commit -> GitHub Actions CI -> Docker image -> Docker Compose
                                |
                                v
+-----------------------------------------------------------+
|                  Docker Compose (Local)                   |
|                                                           |
|  +----------+  +----------+  +------------+  +----------+ |
|  |  MLflow  |  | Serving  |  | Prometheus |  | Grafana  | |
|  |  :5000   |  |  :8000   |  |   :9090    |  |  :3000   | |
|  +----------+  +----------+  +------------+  +----------+ |
|                                                           |
|  +----------------+                                       |
|  |  Pushgateway   |  <- Drift metrics from Evidently      |
|  |     :9091      |                                       |
|  +----------------+                                       |
+-----------------------------------------------------------+
                                |
                                v
+-----------------------------------------------------------+
|                    ML Lifecycle                           |
|                                                           |
| Data validation -> Training -> MLflow tracking            |
| -> Evaluation -> Promotion gate -> Champion model         |
| -> Serving API -> Drift detection -> Retraining           |
+-----------------------------------------------------------+
```

### Runtime Scope

**What runs locally:** MLflow, the serving API, Prometheus, Grafana, Pushgateway, and the training and evaluation workflows.

**What is simulated or omitted:** Kubernetes and Helm manifests, where present, document a production deployment pattern. Docker Compose is the supported local runtime because of the machine's 8 GB RAM constraint. No cloud resources are created. Argo CD GitOps was demonstrated in an earlier phase, but the local kind cluster was removed to free resources.

## Quick Start

### Prerequisites

- Windows 10/11 with WSL 2 and Ubuntu
- Docker Desktop with WSL 2 integration
- Python 3.12+
- `uv`

### Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/KanzaKashaf/ModelOps.git
cd ModelOps
```

Install `uv` if it is not already available:

```bash
python3 -m pip install --user uv
```

If `uv` is not found after installation, reopen the terminal or ensure its installation directory is on your PATH.

Create a virtual environment and install the project:

```bash
uv venv
uv pip install -e ".[dev]"
```

Generate the reference dataset:

```bash
uv run python -m modelops.monitoring.reference
```

Build the serving image:

```bash
chmod +x scripts/build_image.sh
./scripts/build_image.sh
```

Start the services:

```bash
docker compose up -d
```

Check service status:

```bash
docker compose ps
```

Verify the serving API:

```bash
curl -fsS http://localhost:8000/health/live
```

### Service URLs

| Service | Local URL |
|---|---|
| Serving API | http://localhost:8000 |
| API documentation | http://localhost:8000/docs |
| MLflow | http://localhost:5000 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Pushgateway | http://localhost:9091 |

The availability of individual endpoints depends on the Compose configuration and enabled services.

## Run the Full Pipeline

Run these commands from the repository root.

### 1. Train and evaluate candidate models

```bash
uv run python scripts/retrain_and_evaluate.py
```

### 2. Review the evaluation report

```bash
cat reports/retraining_evaluation.json
```

### 3. Promote an approved candidate

```bash
uv run python scripts/promote_model.py manifests/gradient_boosting-v3.json
```

Promotion should follow the evaluation results and the project's governance rules. Confirm that the manifest exists and identifies the intended candidate before running this command.

### 4. Restart the serving service

```bash
docker compose restart serving
```

### 5. Verify the active model

```bash
curl -fsS http://localhost:8000/v1/model/info
```

## What This Demonstrates

| Capability | Implementation |
|---|---|
| Reproducible training | Fixed random seed, deterministic data splitting, Pandera schema validation |
| Experiment tracking | MLflow with SQLite backend, parameters, metrics, tags, and artifacts |
| Model governance | Promotion gates, champion alias, manifests, SHA-256 checksums |
| Model serving | FastAPI, typed schemas, request IDs, health probes |
| CI/CD | GitHub Actions, path-based workflow gating, automated quality checks, security scans |
| Containerisation | Multi-stage Docker build, non-root execution, Trivy scanning |
| Observability | Prometheus metrics, Grafana dashboards, SLO alerts, operational runbooks |
| Drift monitoring | Evidently reports, Pushgateway integration, drift alerts |
| Incident response | Failure drills, postmortems, rollback procedures |
| Retraining | Candidate evaluation pipeline with a human approval gate |

## Documentation

| Document | Path |
|---|---|
| Data card | `docs/data-card.md` |
| Model card | `docs/model-card.md` |
| Model governance | `docs/model-governance.md` |
| Serving API | `docs/serving-api.md` |
| CI/CD | `docs/ci-cd.md` |
| Docker | `docs/docker.md` |
| Monitoring | `docs/monitoring.md` |
| SLOs | `docs/slo.md` |
| Threat model | `docs/threat-model.md` |
| Runbooks | `docs/runbooks/` |
| Release checklist | `docs/release-checklist.md` |
| Incident postmortems | `docs/incidents/` |

## Limitations

- **Local-first, not production:** This is a learning and portfolio platform, not a highly available production system.
- **Hardware constraints:** The Kubernetes/Helm/GitOps environment was demonstrated separately. Docker Compose is the supported local runtime for an 8 GB RAM machine.
- **Public dataset:** The California Housing dataset is used for experimentation; no private user data is required.
- **No cloud resources:** The local workflow does not require AWS, GCP, or Azure resources.
- **Drift is not accuracy:** Data drift indicates a change in input distributions; it does not independently establish a decline in model accuracy.

## License

See the repository for license information.
