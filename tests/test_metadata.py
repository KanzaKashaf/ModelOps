"""Tests for reproducibility metadata collection."""
import pandas as pd

from modelops.tracking.metadata import (
    dependency_versions,
    hash_dataframe,
)


def test_hash_dataframe_is_deterministic():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    h1 = hash_dataframe(df)
    h2 = hash_dataframe(df)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_hash_dataframe_changes_with_data():
    df1 = pd.DataFrame({"a": [1, 2, 3]})
    df2 = pd.DataFrame({"a": [1, 2, 4]})
    assert hash_dataframe(df1) != hash_dataframe(df2)


def test_dependency_versions_contains_keys():
    versions = dependency_versions()
    for key in ["scikit_learn", "numpy", "pandas", "python"]:
        assert key in versions
