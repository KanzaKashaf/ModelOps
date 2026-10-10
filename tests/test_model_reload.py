"""Verify that saved pipelines can be reloaded and used for prediction."""
import joblib
import numpy as np
import pandas as pd
import pytest

from modelops.data.loader import TARGET_COLUMN, load_dataset
from modelops.data.split import split_dataset
from modelops.training.preprocessing import get_feature_columns

ARTIFACT_PATH = "models/gradient_boosting.joblib"


@pytest.fixture(scope="module")
def test_data():
    df = load_dataset()
    _, test_df = split_dataset(df)
    return test_df


def test_reload_and_predict(test_data):
    pipeline = joblib.load(ARTIFACT_PATH)
    features = get_feature_columns(list(test_data.columns))
    X = test_data[features]
    preds = pipeline.predict(X)
    assert len(preds) == len(X)
    assert not np.isnan(preds).any()


def test_reload_no_preprocessing_skew(test_data):
    """Direct pipeline prediction must match manual preprocessing + model."""
    pipeline = joblib.load(ARTIFACT_PATH)
    features = get_feature_columns(list(test_data.columns))
    X = test_data[features]

    direct_preds = pipeline.predict(X)

    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]
    X_transformed = preprocessor.transform(X)
    manual_preds = model.predict(X_transformed)

    np.testing.assert_allclose(direct_preds, manual_preds, rtol=1e-10)