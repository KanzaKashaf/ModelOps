"""Ensure the src layout is on sys.path for test collection.

This is a defense-in-depth measure: even if the editable install fails
to register the package, pytest will still find the source.
"""
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
