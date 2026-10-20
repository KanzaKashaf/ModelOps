# Threat Model — ModelOps Serving Platform

## Scope

This threat model covers the serving API, the model artifact, and
the prediction pipeline. It does not cover the MLflow tracking server,
the CI/CD pipeline, or the Docker Compose infrastructure, which have
separate security controls.

## Assets

| Asset | Description | Impact if Compromised |
|-------|-------------|----------------------|
| Model artifact | `gradient_boosting.joblib` binary | Incorrect predictions, potential code execution |
| Prediction inputs | User-submitted feature vectors | Data poisoning, adversarial examples |
| Prediction outputs | Returned predictions | Information leakage, trust erosion |
| MLflow registry | Model version metadata and aliases | Unauthorized model promotion |
| API credentials | MLflow tracking URI credentials (if any) | Unauthorized registry access |

## Threat Actors

| Actor | Motivation | Capability |
|-------|-----------|------------|
| External attacker | Data theft, service disruption | Network access, crafted requests |
| Malicious insider | Model manipulation | Registry access, artifact write access |
| Accidental insider | Misconfiguration | Deployment permissions |

## Threats and Mitigations

### T1: Model Artifact Tampering

**Threat:** An attacker with write access to the model artifact
directory replaces the model with a malicious binary.

**Mitigation:**
- Model artifact SHA-256 is recorded in the manifest (Phase 2).
- The manifest is committed to Git and immutable.
- The artifact is mounted read-only at `/app/models:ro` (enforced
  by both the Docker volume `:ro` flag and the Kubernetes
  `readOnly: true` mount in the Helm chart).
- The container runs as non-root (UID 1001, `appuser`).
- Verified during Phase 7 Drill 3: `mv` inside the container fails
  with `Read-only file system`.

### T2: Adversarial Prediction Inputs

**Threat:** An attacker sends crafted feature vectors designed to
produce specific incorrect predictions.

**Mitigation:**
- Input schema validation via Pydantic (`extra="forbid"`, exact
  feature count = 8, float type enforced).
- Pandera schema validation (from Phase 1) applies to batch inputs
  and is available at inference time.
- Request-size limiting (64 KB) prevents payload-based exhaustion
  (see T3).
- Drift monitoring (Phase 9) detects distribution shifts that may
  indicate adversarial probing.

**Residual risk:** Adversarial examples that are within the valid
input distribution cannot be detected by schema validation. This
is a known limitation of ML systems and is documented in the
data card (`docs/data-card.md`).

### T3: Denial of Service via Large Payloads

**Threat:** An attacker sends oversized prediction payloads to
exhaust server memory.

**Mitigation:**
- `RequestSizeLimitMiddleware` rejects requests with
  `Content-Length > 64 KB` before the body is read.
- Docker Compose resource limits cap the serving container's
  resource consumption.
- Prometheus alerts on latency (`ServingHighLatencyP95`) and
  error rate (`ServingHighErrorRateFastBurn`).

**Verification:** Phase 10 Step 4 confirmed that a 700 KB payload
returns HTTP 413, while a valid payload returns HTTP 200.

### T4: Model Version Confusion

**Threat:** A stale or unapproved model version is served due to
misconfigured `@champion` alias or `MODELOPS_MODEL_URI`.

**Mitigation:**
- The `@champion` alias is the single deployment contract.
- `modelops_model_info` gauge exposes the served model version.
- Grafana dashboard shows the model version.
- Promotion gate (Phase 2) prevents unapproved models from being
  promoted to `@champion`.
- Fallback behavior is explicit: if the registry is unreachable,
  the API loads the local artifact and logs `model_version: local-fallback`.

### T5: Secret Leakage

**Threat:** MLflow credentials or other secrets are exposed in logs,
responses, or Git.

**Mitigation:**
- No secrets in Git (Gitleaks enforces this in `security-scan` CI job).
- Secrets injected via environment variables, never baked into images.
- Error responses never include stack traces or internal paths.
- `X-Request-ID` correlates logs without exposing sensitive data.
- `k8s/secret.env` and `*.env` are git-ignored.

## Out of Scope

- Network-level attacks (TLS termination, DDoS) — handled by the
  deployment platform in production.
- Supply-chain attacks on base images — partially mitigated by
  digest pinning; full mitigation requires image signing with
  Sigstore/cosign.
- Physical access to the host — assumed trusted for local development.

## Review Cadence

This threat model is a living document. It should be reviewed:
- When a new asset is added (e.g., a new model type).
- When a new external interface is exposed (e.g., a new endpoint).
- When a new threat actor or attack vector is identified.
- At least once per major release.
