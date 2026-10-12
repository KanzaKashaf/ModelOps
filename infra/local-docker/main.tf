# ── Docker Network ──────────────────────────────────────────────────
# The serving container attaches to this network. Terraform infers
# the dependency from the reference docker_network.modelops.name
# inside docker_container.serving and creates the network first.
resource "docker_network" "modelops" {
  name   = var.network_name
  driver = "bridge"

  labels {
    label = "managed-by"
    value = "terraform"
  }

  labels {
    label = "project"
    value = "modelops"
  }
}

# ── Serving Container ───────────────────────────────────────────────
resource "docker_container" "serving" {
  name  = var.container_name
  image = "modelops-serving:${var.image_tag}"

  networks_advanced {
    name = docker_network.modelops.name
  }

  ports {
    internal = var.container_port
    external = var.host_port
    protocol = "tcp"
  }

  # Environment. The concat() merges the required vars with an
  # optional MLflow tracking URI. When var.mlflow_tracking_uri is
  # empty, the second list is empty and the app uses the local
  # fallback model at /app/models.
  env = concat(
    [
      "MODELOPS_MODEL_URI=models:/modelops-housing-regressor@champion",
      "MODELOPS_MODEL_NAME=modelops-housing-regressor",
      "MODELOPS_LOCAL_ARTIFACT_FALLBACK=/app/models/gradient_boosting.joblib",
    ],
    var.mlflow_tracking_uri != "" ? [
      "MODELOPS_MLFLOW_TRACKING_URI=${var.mlflow_tracking_uri}"
    ] : []
  )

  # Mount the model artifact directory read-only if a path was
  # provided. The model is never baked into the image.
  dynamic "volumes" {
    for_each = var.model_path != "" ? [1] : []
    content {
      host_path      = var.model_path
      container_path = "/app/models"
      read_only      = true
    }
  }

  # Resource limits matching the Kubernetes requests/limits that
  # Phase 7 will define, for consistency between environments.
  memory     = var.memory_mb
  cpu_shares = var.cpu_shares

  restart = "unless-stopped"

  healthcheck {
    test         = ["CMD", "curl", "-f", "http://127.0.0.1:8000/health/live"]
    interval     = "30s"
    timeout      = "5s"
    retries      = 3
    start_period = "15s"
  }

  labels {
    label = "managed-by"
    value = "terraform"
  }

  labels {
    label = "project"
    value = "modelops"
  }

  labels {
    label = "application"
    value = "serving"
  }

  # Immutable-tag semantics: changing image_tag replaces the
  # container. Correct for a stateless serving workload.
  lifecycle {
    create_before_destroy = false
  }
}
