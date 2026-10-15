"""Save and load the reference dataset for drift detection.

The reference dataset is the training split. Drift is measured by
comparing recent production inputs against this reference.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from modelops.data.loader import load_dataset
from modelops.data.split import split_dataset

REFERENCE_PATH = Path("data/reference.parquet")


def save_reference(output_dir: Path = Path("data")) -> Path:
    """Save the training split as the reference dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    df = load_dataset()
    train_df, _ = split_dataset(df, test_size=0.2, seed=42)
    path = output_dir / "reference.parquet"
    train_df.to_parquet(path, index=False)
    return path


def load_reference(path: Path = REFERENCE_PATH) -> pd.DataFrame:
    """Load the reference dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Reference dataset not found at {path}. "
            "Run `python -m modelops.monitoring.reference` first."
        )
    return pd.read_parquet(path)


if __name__ == "__main__":
    p = save_reference()
    print(f"Reference dataset saved to {p}")
