from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from data_processing.convert_to_gdf import convert_to_geo_dataframe, load_processed_geo_dataframe


def test_os_geodataframe_csv_roundtrip_restores_points_and_crs(tmp_path: Path):
    original = pd.DataFrame(
        {
            "NAME": ["Example A", "Example B"],
            "GEOMETRY_X": [457077, 436000],
            "GEOMETRY_Y": [1205289, 325000],
        }
    )
    first = convert_to_geo_dataframe(original)
    path = tmp_path / "ordinance_survey_gdf.csv"
    first.to_csv(path, index=False)

    reloaded = load_processed_geo_dataframe(path)

    assert isinstance(reloaded, gpd.GeoDataFrame)
    assert reloaded.crs is not None
    assert reloaded.crs.to_epsg() == 27700
    assert reloaded.geometry.geom_type.tolist() == ["Point", "Point"]
    assert reloaded.geometry.x.tolist() == [457077, 436000]
    assert reloaded.geometry.y.tolist() == [1205289, 325000]
    assert reloaded["NAME"].tolist() == ["Example A", "Example B"]


def test_os_geodataframe_csv_reload_rejects_missing_geometry(tmp_path: Path):
    path = tmp_path / "invalid.csv"
    pd.DataFrame({"NAME": ["Invalid"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="WKT geometry"):
        load_processed_geo_dataframe(path)
