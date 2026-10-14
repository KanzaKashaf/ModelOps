"""Compute data drift between reference and recent data using Evidently.

The drift report is converted to Prometheus metrics and pushed to a
Pushgateway. Prometheus scrapes the Pushgateway and exposes the drift
metrics for Grafana dashboards and alerts.

CRITICAL: Data drift is not proof of accuracy decline. Without
ground-truth labels, we can only detect distribution changes.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

from modelops.monitoring.reference import load_reference

logger = logging.getLogger(__name__)

DEFAULT_PUSHGATEWAY = "localhost:9091"
JOB_NAME = "modelops_drift"


def compute_drift(
    reference: pd.DataFrame,
    recent: pd.DataFrame,
    output_dir: Path = Path("reports"),
) -> dict:
    """Compute data drift on feature columns only.

    The target column is excluded because it is not available at
    inference time. Monitoring target drift would be misleading.
    """
    from modelops.data.loader import TARGET_COLUMN

    output_dir.mkdir(parents=True, exist_ok=True)

    ref = reference.drop(columns=[TARGET_COLUMN], errors="ignore")
    cur = recent.drop(columns=[TARGET_COLUMN], errors="ignore")

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=cur)

    html_path = output_dir / "drift_report.html"
    json_path = output_dir / "drift_report.json"
    report.save_html(str(html_path))
    report.save_json(str(json_path))

    report_dict = report.as_dict()
    metrics = report_dict.get("metrics", []) if isinstance(report_dict, dict) else []

    # Evidently 0.4.x may emit DatasetDriftMetric or DataDriftTable.
    for metric in metrics:
        name = metric.get("metric")
        if name in ("DataDriftTable", "DatasetDriftMetric"):
            r = metric.get("result", {})
            share = (
                r.get("share_of_drifted_columns")
                or r.get("drift_share")
                or 0.0
            )
            n_drifted = (
                r.get("number_of_drifted_columns")
                or r.get("count_of_drifted_columns")
                or 0
            )
            n_columns = r.get("number_of_columns") or 0
            return {
                "dataset_drift": bool(r.get("dataset_drift", False)),
                "share_drifted": float(share),
                "n_drifted": int(n_drifted),
                "n_columns": int(n_columns),
            }

    logger.warning("No drift metric found in Evidently report; returning zeros")
    return {"dataset_drift": False, "share_drifted": 0.0, "n_drifted": 0, "n_columns": 0}


def push_drift_metrics(summary: dict, gateway: str = DEFAULT_PUSHGATEWAY) -> None:
    """Push drift metrics to a Prometheus Pushgateway."""
    registry = CollectorRegistry()
    g_share = Gauge(
        "modelops_drift_share",
        "Share of features with detected drift",
        registry=registry,
    )
    g_drifted = Gauge(
        "modelops_drifted_columns",
        "Number of features with detected drift",
        registry=registry,
    )
    g_total = Gauge(
        "modelops_total_columns",
        "Total number of features monitored",
        registry=registry,
    )
    g_share.set(summary["share_drifted"])
    g_drifted.set(summary["n_drifted"])
    g_total.set(summary["n_columns"])

    push_to_gateway(gateway, job=JOB_NAME, registry=registry)
    logger.info("Pushed drift metrics to %s", gateway)


def run_drift_check(recent_path: Path, gateway: str = DEFAULT_PUSHGATEWAY) -> dict:
    reference = load_reference()
    recent = pd.read_parquet(recent_path)
    summary = compute_drift(reference, recent)
    logger.info("Drift summary: %s", json.dumps(summary, indent=2))
    push_drift_metrics(summary, gateway=gateway)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="ModelOps drift detection")
    parser.add_argument("--recent", type=Path, required=True)
    parser.add_argument("--gateway", type=str, default=DEFAULT_PUSHGATEWAY)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    summary = run_drift_check(args.recent, gateway=args.gateway)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
