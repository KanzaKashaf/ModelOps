terraform {
  required_version = ">= 1.6.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 4.6"
    }
  }
}

provider "docker" {
  # Connects to the local Docker daemon by default via
  # /var/run/docker.sock. This is what Docker Desktop exposes
  # to WSL 2 when integration is enabled.
}
