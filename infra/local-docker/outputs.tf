output "container_id" {
  description = "ID of the serving container."
  value       = docker_container.serving.id
}

output "container_name" {
  description = "Name of the serving container."
  value       = docker_container.serving.name
}

output "host_port" {
  description = "Host port mapped to the serving API."
  value       = var.host_port
}

output "api_url" {
  description = "Base URL for the serving API."
  value       = "http://127.0.0.1:${var.host_port}"
}

output "health_live_url" {
  description = "Liveness endpoint URL."
  value       = "http://127.0.0.1:${var.host_port}/health/live"
}

output "health_ready_url" {
  description = "Readiness endpoint URL."
  value       = "http://127.0.0.1:${var.host_port}/health/ready"
}

output "metrics_url" {
  description = "Prometheus metrics endpoint URL."
  value       = "http://127.0.0.1:${var.host_port}/metrics"
}

output "network_name" {
  description = "Name of the Docker network."
  value       = docker_network.modelops.name
}
