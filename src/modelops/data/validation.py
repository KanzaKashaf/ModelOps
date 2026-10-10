"""Schema validation for the California Housing dataset using pandera."""
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame, Series

from modelops.data.loader import TARGET_COLUMN


class HousingSchema(pa.DataFrameModel):
    """Expected schema for the California Housing dataset."""

    MedInc: Series[float] = pa.Field(ge=0, nullable=False)
    HouseAge: Series[float] = pa.Field(ge=0, nullable=False)
    AveRooms: Series[float] = pa.Field(ge=0, nullable=False)
    AveBedrms: Series[float] = pa.Field(ge=0, nullable=False)
    Population: Series[float] = pa.Field(ge=0, nullable=False)
    AveOccup: Series[float] = pa.Field(ge=0, nullable=False)
    Latitude: Series[float] = pa.Field(ge=32, le=42, nullable=False)
    Longitude: Series[float] = pa.Field(ge=-125, le=-114, nullable=False)
    MedHouseValue: Series[float] = pa.Field(ge=0, le=5.1, nullable=False)

    class Config:
        strict = True
        # coerce = True


def validate_dataset(df: pd.DataFrame) -> DataFrame[HousingSchema]:
    """Validate the raw dataset against the schema.

    Raises ``pandera.errors.SchemaError`` if validation fails.
    """
    return HousingSchema.validate(df)


def validate_prediction_input(df: pd.DataFrame) -> DataFrame[HousingSchema]:
    """Validate inference-time input (features only).

    The target column is not expected at inference time.
    """
    features = [c for c in HousingSchema.to_schema().columns if c != TARGET_COLUMN]
    schema = HousingSchema.to_schema().remove_columns([TARGET_COLUMN])
    return schema.validate(df[features])
