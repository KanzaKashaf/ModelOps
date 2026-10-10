# """Tests for deterministic splitting."""
# import pandas as pd

# from modelops.data.loader import load_dataset
# from modelops.data.split import split_dataset


# def test_split_is_deterministic():
#     df = load_dataset()
#     train_a, test_a = split_dataset(df)
#     train_b, test_b = split_dataset(df)
#     pd.testing.assert_frame_equal(train_a, train_b)
#     pd.testing.assert_frame_equal(test_a, test_b)


# def test_split_sizes():
#     df = load_dataset()
#     train, test = split_dataset(df, test_size=0.2)
#     assert len(train) == 16512
#     assert len(test) == 4128


# def test_no_overlap():
#     df = load_dataset()
#     train, test = split_dataset(df)
#     train_idx = set(train.index)
#     test_idx = set(test.index)
#     assert train_idx.isdisjoint(test_idx)

"""Tests for deterministic splitting."""

import pandas as pd

from modelops.data.loader import load_dataset
from modelops.data.split import split_dataset


def test_split_is_deterministic():
    """Repeated splits with the same seed must produce identical results."""
    df = load_dataset()

    train_a, test_a = split_dataset(df)
    train_b, test_b = split_dataset(df)

    pd.testing.assert_frame_equal(train_a, train_b)
    pd.testing.assert_frame_equal(test_a, test_b)


def test_split_sizes():
    """Verify that the dataset is split into the expected sizes."""
    df = load_dataset()

    train, test = split_dataset(df, test_size=0.2)

    assert len(train) == 16512
    assert len(test) == 4128


def test_no_overlap():
    """Verify that no original row belongs to both splits."""
    df = load_dataset()

    train, test = split_dataset(df)

    train_idx = set(train.index)
    test_idx = set(test.index)

    assert train_idx.isdisjoint(test_idx)

    # Every original row must belong to exactly one split.
    assert len(train) + len(test) == len(df)
    assert train_idx | test_idx == set(df.index)