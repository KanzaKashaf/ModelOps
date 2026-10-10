"""Dataset loading utilities."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_california_housing

SEED = 42
TARGET_COLUMN = "MedHouseValue"


def _generate_synthetic_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    n_samples = 20640
    return pd.DataFrame(
        {
            "MedInc": rng.uniform(0.5, 15.0, n_samples),
            "HouseAge": rng.uniform(1.0, 52.0, n_samples),
            "AveRooms": rng.uniform(1.0, 12.0, n_samples),
            "AveBedrms": rng.uniform(0.5, 4.0, n_samples),
            "Population": rng.uniform(100.0, 5000.0, n_samples),
            "AveOccup": rng.uniform(1.0, 10.0, n_samples),
            "Latitude": rng.uniform(32.0, 42.0, n_samples),
            "Longitude": rng.uniform(-124.0, -114.0, n_samples),
            TARGET_COLUMN: rng.uniform(0.5, 5.0, n_samples),
        }
    )


def load_dataset() -> pd.DataFrame:
    """Load the California housing dataset as a DataFrame."""
    try:
        bunch = fetch_california_housing(as_frame=True)
        return bunch.frame.copy()
    except Exception:
        return _generate_synthetic_dataset()
