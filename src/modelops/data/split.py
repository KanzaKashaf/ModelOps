"""Deterministic dataset splitting."""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from modelops.data.loader import SEED


def split_dataset(
    df: pd.DataFrame, test_size: float = 0.2, seed: int = SEED
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a dataset into deterministic train/test DataFrames."""
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=seed)
    return train_df, test_df

