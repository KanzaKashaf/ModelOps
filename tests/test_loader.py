"""Tests for dataset loading fallback behavior."""

from modelops.data import loader


def test_load_dataset_falls_back_when_fetch_raises(monkeypatch):
    """Any fetch failure should trigger deterministic synthetic fallback."""

    def _raise_fetch_error(*args, **kwargs):
        raise RuntimeError("simulated fetch failure")

    monkeypatch.setattr(loader, "fetch_california_housing", _raise_fetch_error)

    df = loader.load_dataset()

    assert not df.empty
    assert loader.TARGET_COLUMN in df.columns
    assert len(df) == 20640
