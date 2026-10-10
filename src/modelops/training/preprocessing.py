"""Preprocessing pipeline builder.

The pipeline is fitted on training data only and saved with the model
to guarantee identical transformations at inference time.
"""
from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from modelops.data.loader import TARGET_COLUMN


def build_preprocessor(feature_columns: list[str]) -> ColumnTransformer:
    """Build a numeric preprocessing pipeline.

    Steps:
    1. Median imputation (safety net for missing values).
    2. Standard scaling.

    All steps are fitted **only** on the training split.
    """
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        transformers=[("numeric", numeric_pipeline, feature_columns)],
        remainder="drop",
    )


def get_feature_columns(df_columns: list[str]) -> list[str]:
    """Return feature column names, excluding the target."""
    return [c for c in df_columns if c != TARGET_COLUMN]
