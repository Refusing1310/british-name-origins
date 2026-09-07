
from pathlib import Path

import geopandas as gpd
import pandas as pd


def _load_dataframe(data) -> pd.DataFrame:
    """Load a dataframe from a DataFrame, path, or file-like object."""
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if hasattr(data, "read"):
        return pd.read_csv(data)
    if isinstance(data, (str, Path)):
        return pd.read_csv(Path(data))
    raise TypeError("Expected a pandas DataFrame, path, or file-like object")


def convert_to_geo_dataframe(df1):
    """Convert a DataFrame to a GeoDataFrame."""
    df1 = _load_dataframe(df1)
    if "GEOMETRY_X" not in df1.columns or "GEOMETRY_Y" not in df1.columns:
        raise ValueError("DataFrame must contain 'GEOMETRY_X' and 'GEOMETRY_Y' columns.")
    gdf = gpd.GeoDataFrame(
        df1,
        geometry=gpd.points_from_xy(df1["GEOMETRY_X"], df1["GEOMETRY_Y"]),
        crs="EPSG:27700", # British National Grid
    )

    # Drop the original coordinate columns after creating the geometry
    gdf = gdf.drop(columns=["GEOMETRY_X", "GEOMETRY_Y"], errors='ignore')

    return gdf