"""Collect reproducibility metadata for MLflow runs."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path

import pandas as pd


def git_commit_hash() -> str:
    """Return the full SHA of the current HEAD commit."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, cwd=Path.cwd()
        ).strip()
    except Exception:
        return "unknown"


def git_branch() -> str:
    """Return the current Git branch name."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, cwd=Path.cwd()
        ).strip()
    except Exception:
        return "unknown"


def hash_dataframe(df: pd.DataFrame) -> str:
    """Compute a deterministic SHA-256 hash of a DataFrame.

    Uses pandas' hash_pandas_object for row-wise deterministic hashing,
    then hashes the resulting array to produce a single digest.
    """
    row_hashes = pd.util.hash_pandas_object(df, index=False)
    digest = hashlib.sha256(row_hashes.values.tobytes()).hexdigest()
    return digest


def hash_file(path: Path | str) -> str:
    """Compute SHA-256 of a file on disk."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def dependency_versions() -> dict[str, str]:
    """Return versions of key ML dependencies."""
    import numpy
    import pandas
    import pandera
    import sklearn

    return {
        "scikit_learn": sklearn.__version__,
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "pandera": pandera.__version__,
        "python": platform.python_version(),
    }


def collect_run_metadata(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    """Collect all reproducibility metadata for a training run."""
    return {
        "git_commit": git_commit_hash(),
        "git_branch": git_branch(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "train_data_hash": hash_dataframe(train_df),
        "test_data_hash": hash_dataframe(test_df),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "dependency_versions": json.dumps(dependency_versions()),
    }
