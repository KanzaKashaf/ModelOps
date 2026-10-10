# Start a local MLflow tracking server with SQLite backend.
# Run this in a separate PowerShell terminal and leave it running.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$mlflowDb = Join-Path $repoRoot "mlflow.db"
$artifactRoot = Join-Path $repoRoot "mlruns"

Write-Host "Starting MLflow server..."
Write-Host "  Backend store: sqlite:///$mlflowDb"
Write-Host "  Artifact root: $artifactRoot"
Write-Host "  Host: 127.0.0.1"
Write-Host "  Port: 5000"

# Use python -m mlflow to avoid WDAC blocking mlflow.exe on Windows.
python -m mlflow server `
    --host 127.0.0.1 `
    --port 5000 `
    --backend-store-uri "sqlite:///$mlflowDb" `
    --default-artifact-root "$artifactRoot"