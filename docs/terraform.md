# Terraform — Infrastructure as Code

## What Terraform Manages

| Resource | Managed | Notes |
|----------|---------|-------|
| Docker network (`modelops-tf-network`) | ✅ Yes | `docker_network.modelops` |
| Docker container (serving) | ✅ Yes | `docker_container.serving` |
| Docker image | ❌ No | Built by `scripts/build_image.sh` |
| Docker volumes (MLflow, Prometheus, Grafana) | ❌ No | Managed by Docker Compose (Phase 5) |
| Kubernetes cluster | ❌ No | Managed in Phase 7 |
| Cloud infrastructure | ❌ No | Not configured |

**This is a local Docker exercise.** It creates no cloud resources.
A production deployment would require VPC, IAM, load balancer, and
managed database resources that are out of scope for this phase.

## Provider

| Attribute | Value |
|-----------|-------|
| Provider | `kreuzwerker/docker` |
| Version constraint | `~> 4.6` |
| Installed version | `4.6.0` |
| Maintainer | Community (transferred from HashiCorp) |

The provider communicates with the Docker daemon over
`/var/run/docker.sock`, which Docker Desktop exposes to WSL 2 when
integration is enabled.

## Directory Layout

nfra/local-docker/
├── .terraform.lock.hcl # Provider version + hashes (committed)
├── main.tf # Network and container resources
├── outputs.tf # 8 outputs (URLs, IDs, port)
├── terraform.tfvars.example # Template for local overrides
├── variables.tf # 9 input variables
└── versions.tf # Provider and Terraform version constraints


## State

- **Backend:** local (`terraform.tfstate`).
- **Location:** `infra/local-docker/terraform.tfstate`.
- **Not committed.** `.gitignore` excludes `*.tfstate`, `*.tfstate.*`,
  `*.tfplan`, `.terraform/`, `terraform.tfvars`.
- **No remote backend.** A production setup would use S3 + DynamoDB
  (or Terraform Cloud) for state locking, encryption, and multi-operator
  safety.
- **Treat as sensitive.** The state file records resource attributes.
  In a cloud configuration, it would contain access keys and other
  secrets. Never commit it, never share it, never edit it by hand.

## Workflow

```bash
cd infra/local-docker

# 1. Initialize provider
terraform init

# 2. Format (canonical)
terraform fmt -recursive

# 3. Validate
terraform validate

# 4. Plan
GIT_SHA=$(git rev-parse --short HEAD)
MODEL_PATH="$(pwd)/../../models"
terraform plan \
  -var="image_tag=${GIT_SHA}" \
  -var="model_path=${MODEL_PATH}"

# 5. Apply (local learning exercise)
terraform apply \
  -var="image_tag=${GIT_SHA}" \
  -var="model_path=${MODEL_PATH}"

# 6. Teardown
terraform destroy \
  -var="image_tag=${GIT_SHA}" \
  -var="model_path=${MODEL_PATH}"