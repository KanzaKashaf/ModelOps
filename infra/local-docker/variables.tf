variable "image_tag" {
  description = "Docker image tag for the serving application. Pass the Git short SHA when applying."
  type        = string
  default     = "latest"
}

variable "container_name" {
  description = "Name of the serving container."
  type        = string
  default     = "modelops-serving-tf"
}

variable "host_port" {
  description = "Host port mapped to the container's application port."
  type        = number
  default     = 8000
}

variable "container_port" {
  description = "Application port inside the container."
  type        = number
  default     = 8000
}

variable "model_path" {
  description = "Absolute path on the host to the model artifact directory. Empty disables the volume mount."
  type        = string
  default     = ""
}

variable "mlflow_tracking_uri" {
  description = "MLflow tracking server URI. Empty means use the local fallback."
  type        = string
  default     = ""
}

variable "network_name" {
  description = "Name of the Docker network for the stack."
  type        = string
  default     = "modelops-tf-network"
}

variable "memory_mb" {
  description = "Container memory limit in megabytes."
  type        = number
  default     = 512
}

variable "cpu_shares" {
  description = "Container CPU shares (1024 = 1 full CPU)."
  type        = number
  default     = 512
}
