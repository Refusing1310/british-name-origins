"""Source lineage must remain auditable when derivations are aggregated."""
import pandas as pd

from data_processing.process_csvs import process_kepn_data


def test_source_lineage_retains_homonymous_places_and_every_element_occurrence(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir()
    processed = tmp_path / "data" / "processed"
    pd.DataFrame([
        {"PlaceName": "Hamton", "Etymology": "",
         "Derivation": "ham Old English - A home; tūn Old English - An enclosure"},
        {"PlaceName": "Twoforms", "Etymology": "",
         "Derivation": "fox/foxes Old English - A fox"},
    ]).to_csv(raw / "a.csv", index=False)
    pd.DataFrame([
        {"PlaceName": "Hamton", "Etymology": "",
         "Derivation": "ham Old English - A home; an C; eccles Celtic"},
        {"PlaceName": "Otherham", "Etymology": "",
         "Derivation": "ham Old Norse - A homestead"},
    ]).to_csv(raw / "b.csv", index=False)

    ground_truth, elements = process_kepn_data(raw, processed)
    links = pd.read_csv(processed / "element_sources.csv")

    assert ground_truth["KEPNSourceFile"].tolist() == ["a.csv", "a.csv", "b.csv", "b.csv"]
    assert ground_truth["KEPNRecordNumber"].tolist() == [1, 2, 1, 2]
    assert list(links.columns) == [
        "GroundTruthRow", "KEPNSourceFile", "KEPNRecordNumber",
        "ElementId", "OccurrenceInRow",
    ]
    assert sorted(links["GroundTruthRow"].unique()) == [0, 1, 2, 3]

    # Every added occurrence corresponds to exactly one count in elements.csv.
    frequency = elements.set_index("Id")["Frequency"].to_dict()
    assert links.groupby("ElementId").size().to_dict() == frequency
    assert set(links["ElementId"]) == set(elements["Id"])
    assert links.groupby("GroundTruthRow")["OccurrenceInRow"].apply(list).tolist() == [
        [1, 2], [1, 2], [1, 2, 3], [1],
    ]

    ham = elements.loc[
        (elements["Element"] == "ham") & (elements["Language"] == "Old English")
    ].iloc[0]
    rows = links.loc[links["ElementId"] == ham["Id"]]
    assert rows["GroundTruthRow"].tolist() == [0, 2]
    assert rows["KEPNSourceFile"].tolist() == ["a.csv", "b.csv"]
    assert ham["Frequency"] == 2

    assert elements.loc[elements["Element"] == "an", "Language"].tolist() == ["C"]
    assert elements.loc[elements["Element"] == "eccles", "Language"].tolist() == ["Celtic"]
    # Round-tripping CSV preserves values but may infer different string dtypes.
    pd.testing.assert_frame_equal(
        pd.read_csv(processed / "ground_truth.csv"), ground_truth, check_dtype=False
    )
    assert set(pd.read_csv(processed / "elements.csv")["Id"]) == set(links["ElementId"])


def test_missing_derivation_produces_header_only_lineage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir()
    pd.DataFrame([
        {"PlaceName": "Unknown", "Etymology": "", "Derivation": None},
    ]).to_csv(raw / "one.csv", index=False)
    processed = tmp_path / "data" / "processed"

    ground_truth, elements = process_kepn_data(raw, processed)
    assert len(ground_truth) == 1
    assert elements.empty
    links = pd.read_csv(processed / "element_sources.csv")
    assert links.empty
    assert list(links.columns) == [
        "GroundTruthRow", "KEPNSourceFile", "KEPNRecordNumber",
        "ElementId", "OccurrenceInRow",
    ]


def test_source_fields_are_opt_in_for_generic_os_combiner(tmp_path):
    from data_processing.process_csvs import combine_csvs_to_dataframe
    folder = tmp_path / "raw"
    folder.mkdir()
    pd.DataFrame({"Example": ["one"]}).to_csv(folder / "a.csv", index=False)
    ordinary = combine_csvs_to_dataframe(
        folder, separate_header_file=False, ignored_columns=[]
    )
    assert ordinary.columns.tolist() == ["Example"]
