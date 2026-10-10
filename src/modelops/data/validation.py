"""Dataset validation rules."""
from __future__ import annotations

import pandas as pd
import pandera as pa
from pandera import Check

from modelops.data.loader import TARGET_COLUMN

_SCHEMA = pa.DataFrameSchema(
    {
        "MedInc": pa.Column(float, checks=Check.ge(0.0)),
        "HouseAge": pa.Column(float),
        "AveRooms": pa.Column(float),
        "AveBedrms": pa.Column(float),
        "Population": pa.Column(float),
        "AveOccup": pa.Column(float),
        "Latitude": pa.Column(float),
        "Longitude": pa.Column(float),
        TARGET_COLUMN: pa.Column(float),
    },
    strict=True,
)


def validate_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Validate expected schema and value constraints."""
    return _SCHEMA.validate(df)

