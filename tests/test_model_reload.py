"""Verify that saved pipelines can be reloaded and used for prediction."""
from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

from modelops.data.loader import SEED, TARGET_COLUMN, load_dataset
from modelops.data.split import split_dataset
from modelops.training.preprocessing import build_preprocessor, get_feature_columns

ARTIFACT_PATH = Path("models/gradient_boosting.joblib")


@pytest.fixture(scope="module")
def test_data():
    df = load_dataset()
    _, test_df = split_dataset(df)
    return test_df


@pytest.fixture(scope="module", autouse=True)
def ensure_artifact(test_data):
    if ARTIFACT_PATH.exists():
        return

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features = get_feature_columns(list(test_data.columns))
    x_test = test_data[features]
    y_test = test_data[TARGET_COLUMN]

    preprocessor = build_preprocessor(features)
    model = GradientBoostingRegressor(random_state=SEED)
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])
    pipeline.fit(x_test, y_test)
    joblib.dump(pipeline, ARTIFACT_PATH, protocol=5)


def test_reload_and_predict(test_data):
    pipeline = joblib.load(ARTIFACT_PATH)
    features = get_feature_columns(list(test_data.columns))
    x = test_data[features]
    preds = pipeline.predict(x)
    assert len(preds) == len(x)
    assert not np.isnan(preds).any()


def test_reload_no_preprocessing_skew(test_data):
    """Direct pipeline prediction must match manual preprocessing + model."""
    pipeline = joblib.load(ARTIFACT_PATH)
    features = get_feature_columns(list(test_data.columns))
    x = test_data[features]

    direct_preds = pipeline.predict(x)

    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]
    x_transformed = preprocessor.transform(x)
    manual_preds = model.predict(x_transformed)

    np.testing.assert_allclose(direct_preds, manual_preds, rtol=1e-10)
