"""Generate a human-readable evaluation report from training metrics."""
from __future__ import annotations

import json
from pathlib import Path


def generate_report(metrics_path: str = "reports/training_metrics.json") -> str:
    metrics = json.loads(Path(metrics_path).read_text())
    lines = [
        "# Model Evaluation Report",
        "",
        "| Model | Test MAE | Test RMSE | Test R² |",
        "|-------|----------|-----------|---------|",
    ]
    for name, m in metrics.items():
        t = m["test"]
        lines.append(f"| {name} | {t['mae']:.4f} | {t['rmse']:.4f} | {t['r2']:.4f} |")
    lines.append("")
    lines.append(f"Seed: {list(metrics.values())[0]['seed']}")
    lines.append(f"Git commit: {list(metrics.values())[0]['git_commit']}")
    lines.append(f"Python: {list(metrics.values())[0]['python_version']}")
    report = "\n".join(lines)
    out = Path("reports/evaluation_report.md")
    out.write_text(report)
    return report


if __name__ == "__main__":
    print(generate_report())
