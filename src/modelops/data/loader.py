"""Dataset loading and initial inspection for the ModelOps platform."""
from __future__ import annotations

import pandas as pd
from sklearn.datasets import fetch_california_housing

SEED = 42
TARGET_COLUMN = "MedHouseValue"


def load_dataset(as_frame: bool = True) -> pd.DataFrame:
    """Load the California Housing dataset as a pandas DataFrame.

    Returns a DataFrame with feature columns and the target column
    ``MedHouseValue`` (median house value in $100,000s).
    """
    bunch = fetch_california_housing(as_frame=as_frame)
    df = bunch.frame.copy()
    df = df.rename(columns={"MedHouseVal": TARGET_COLUMN})
    return df


def dataset_summary(df: pd.DataFrame) -> dict:
    """Return a compact summary for the data card."""
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "features": [c for c in df.columns if c != TARGET_COLUMN],
        "target": TARGET_COLUMN,
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
