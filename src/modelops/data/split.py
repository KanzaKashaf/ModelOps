# """Deterministic train/test splitting."""
# from __future__ import annotations

# import pandas as pd
# from sklearn.model_selection import train_test_split

# from modelops.data.loader import SEED, TARGET_COLUMN


# def split_dataset(
#     df: pd.DataFrame,
#     test_size: float = 0.2,
#     seed: int = SEED,
# ) -> tuple[pd.DataFrame, pd.DataFrame]:
#     """Split into train and test sets with a fixed seed.

#     The split is performed **before** any preprocessing to prevent
#     data leakage.
#     """
#     train_df, test_df = train_test_split(
#         df,
#         test_size=test_size,
#         random_state=seed,
#         shuffle=True,
#     )
#     return train_df.reset_index(drop=True), test_df.reset_index(drop=True)

"""Deterministic train/test splitting."""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from modelops.data.loader import SEED


def split_dataset(
    df: pd.DataFrame,
    test_size: float = 0.2,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into train and test sets with a fixed seed.

    The split is performed before any preprocessing to prevent
    data leakage.

    Original indexes are preserved so that the training and testing
    rows can be traced back to their positions in the original dataset.
    """
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=seed,
        shuffle=True,
    )

    return train_df, test_df