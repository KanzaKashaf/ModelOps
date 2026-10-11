# Serving API

FastAPI application that loads the champion model from the MLflow
Model Registry and exposes versioned prediction and metadata endpoints.

## Endpoints

| Method | Path              | Purpose                                      |
|--------|-------------------|----------------------------------------------|
| GET    | `/`               | Service information                          |
| GET    | `/health/live`    | Liveness probe (always 200 if process alive) |
| GET    | `/health/ready`   | Readiness probe (503 until model is ready)   |
| GET    | `/v1/model/info`  | Model metadata (name, version, features)     |
| POST   | `/v1/predict`     | Prediction with validated input              |
| GET    | `/metrics`        | Prometheus metrics                           |
| GET    | `/docs`           | OpenAPI documentation                        |

## Running the API

```bash
# In WSL or Linux
python -m modelops.serving