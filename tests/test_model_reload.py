# """Verify that saved pipelines can be reloaded and used for prediction."""
# import joblib
# import numpy as np
# import pytest

# from modelops.data.loader import load_dataset
# from modelops.data.split import split_dataset
# from modelops.training.preprocessing import get_feature_columns

# ARTIFACT_PATH = "models/gradient_boosting.joblib"


# @pytest.fixture(scope="module")
# def test_data():
#     df = load_dataset()
#     _, test_df = split_dataset(df)
#     return test_df


# def test_reload_and_predict(test_data):
#     pipeline = joblib.load(ARTIFACT_PATH)
#     features = get_feature_columns(list(test_data.columns))
#     x = test_data[features]
#     preds = pipeline.predict(x)
#     assert len(preds) == len(x)
#     assert not np.isnan(preds).any()


# def test_reload_no_preprocessing_skew(test_data):
#     """Direct pipeline prediction must match manual preprocessing + model."""
#     pipeline = joblib.load(ARTIFACT_PATH)
#     features = get_feature_columns(list(test_data.columns))
#     x = test_data[features]

#     direct_preds = pipeline.predict(x)

#     preprocessor = pipeline.named_steps["preprocessor"]
#     model = pipeline.named_steps["model"]
#     x_transformed = preprocessor.transform(x)
#     manual_preds = model.predict(x_transformed)

#     np.testing.assert_allclose(direct_preds, manual_preds, rtol=1e-10)


"""Verify that saved pipelines can be reloaded and used for prediction.

These tests require a trained model artifact. They are skipped if the
artifact does not exist, so that the pure-code CI job can pass without
needing to train a model first. The data-and-model CI job trains the
model and then runs these tests against the real artifact.
"""
from pathlib import Path

import joblib
import numpy as np
import pytest

from modelops.data.loader import load_dataset
from modelops.data.split import split_dataset
from modelops.training.preprocessing import get_feature_columns

ARTIFACT_PATH = Path("models/gradient_boosting.joblib")

pytestmark = pytest.mark.skipif(
    not ARTIFACT_PATH.exists(),
    reason=f"Model artifact not found at {ARTIFACT_PATH}. Run training first.",
)


@pytest.fixture(scope="module")
def test_data():
    df = load_dataset()
    _, test_df = split_dataset(df)
    return test_df


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
