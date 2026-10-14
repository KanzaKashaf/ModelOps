"""Generate a synthetic drifted dataset for testing drift detection.

The shift is applied to MedInc (scaled by 1.5) and AveRooms
(scaled by 0.8). Both are common features; the shift is large enough
to trigger the Evidently drift detector.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from modelops.monitoring.reference import load_reference

DRIFTED_PATH = Path("data/recent_drifted.parquet")


def generate_drifted(n_samples: int = 1000, seed: int = 99) -> pd.DataFrame:
    reference = load_reference()
    sample = reference.sample(n=n_samples, random_state=seed).copy()
    sample["MedInc"] = sample["MedInc"] * 1.5
    sample["AveRooms"] = sample["AveRooms"] * 0.8
    return sample


if __name__ == "__main__":
    df = generate_drifted()
    df.to_parquet(DRIFTED_PATH, index=False)
    print(f"Generated {len(df)} drifted rows at {DRIFTED_PATH}")
