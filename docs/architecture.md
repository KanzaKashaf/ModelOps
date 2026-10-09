# Architecture Overview

```mermaid
graph TD
    A[Data Source] --> B[Data Validation]
    B --> C[Training Pipeline]
    C --> D[MLflow Tracking]
    C --> E[Model Artifact]
    E --> F[FastAPI Serving]
    F --> G[Docker Container]
    G --> H[Kubernetes / kind]
    H --> I[Prometheus & Grafana]
    D --> J[Model Registry / Manifest]
    J --> K[Promotion Gate]
    K --> F