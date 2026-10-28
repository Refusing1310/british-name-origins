
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

def load_processed_geo_dataframe(csv_path: str | Path) -> gpd.GeoDataFrame:
    """Restore Point geometry and British National Grid CRS after CSV serialization."""
    df = pd.read_csv(csv_path)
    if "geometry" not in df.columns:
        raise ValueError("Processed OS CSV must have a WKT geometry column.")
    geometry = gpd.GeoSeries.from_wkt(df["geometry"], crs="EPSG:27700")
    return gpd.GeoDataFrame(df.drop(columns=["geometry"]), geometry=geometry, crs="EPSG:27700")
