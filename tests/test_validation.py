# """Tests for data validation."""
# import pytest

# from modelops.data.loader import load_dataset
# from modelops.data.validation import validate_dataset
# from pandera.errors import SchemaError


# def test_valid_dataset_passes():
#     df = load_dataset()
#     validated = validate_dataset(df)
#     assert validated.shape[0] == df.shape[0]


# def test_missing_column_rejected():
#     df = load_dataset().drop(columns=["MedInc"])
#     with pytest.raises(SchemaError):
#         validate_dataset(df)


# def test_negative_value_rejected():
#     df = load_dataset()
#     df.loc[0, "MedInc"] = -1.0
#     with pytest.raises(SchemaError):
#         validate_dataset(df)


# def test_wrong_dtype_rejected():
#     df = load_dataset()
#     df["MedInc"] = df["MedInc"].astype(str)
#     with pytest.raises(SchemaError):
#         validate_dataset(df)


"""Tests for data validation."""

import pytest
from pandera.errors import SchemaError

from modelops.data.loader import load_dataset
from modelops.data.validation import validate_dataset


def test_valid_dataset_passes():
    df = load_dataset()
    validated = validate_dataset(df)
    assert validated.shape[0] == df.shape[0]


def test_missing_column_rejected():
    df = load_dataset().drop(columns=["MedInc"])
    with pytest.raises(SchemaError):
        validate_dataset(df)


def test_negative_value_rejected():
    df = load_dataset()
    df.loc[0, "MedInc"] = -1.0
    with pytest.raises(SchemaError):
        validate_dataset(df)


def test_wrong_dtype_rejected():
    df = load_dataset()
    df["MedInc"] = df["MedInc"].astype(str)
    with pytest.raises(SchemaError):
        validate_dataset(df)
