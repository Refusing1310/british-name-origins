"""Load the sample town dataset and enrich it with name-origin classifications.

The real project is intended to consume Ordnance Survey OpenNames and ONS
population data (which live under ``data/raw/`` and are git-ignored). Until that
pipeline exists, this module ships a small curated CSV of well-known British
towns and cities so the map can be demonstrated end to end without any external
downloads.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from british_names.origins import ORIGIN_COLORS, classify_origin, color_hex

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SAMPLE_CSV = DATA_DIR / "towns_sample.csv"


def load_towns(csv_path: Path | str | None = None) -> pd.DataFrame:
    """Load towns and add ``origin``, ``color`` and ``color_hex`` columns.

    Parameters
    ----------
    csv_path:
        Optional path to a CSV with ``name``, ``lat``, ``lon`` and
        ``population`` columns. Defaults to the bundled sample dataset.
    """

    path = Path(csv_path) if csv_path is not None else SAMPLE_CSV
    df = pd.read_csv(path)

    required = {"name", "lat", "lon", "population"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")

    df["origin"] = df["name"].apply(lambda n: classify_origin(n).value)
    df["color"] = df["name"].apply(
        lambda n: list(ORIGIN_COLORS[classify_origin(n)])
    )
    df["color_hex"] = df["name"].apply(lambda n: color_hex(classify_origin(n)))
    return df
