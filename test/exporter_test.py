"""Tests of the exporter module."""
import os
from test.mocks import set_up_ok_mocks

from StaticNarrative.exporter.exporter import NarrativeExporter
from StaticNarrative.narrative_ref import NarrativeRef

USER_ID = "some_user"
TOKEN = "some_token"  # noqa: S105


def test_exporter_ok(config: dict[str, str], scratch_dir: str, requests_mock) -> None:
    ws_id = 43666
    ref_to_file = {
        "43666/1/21": "data/43666/narrative-43666.1.21.json",
        "43666/1/18": "data/43666/narrative-43666.1.18.json",
        "43666/3/1": "data/43666/report-43666.3.1.json",
        "43666/7/1": "data/43666/report-43666.7.1.json",
    }
    ref_to_info = {}
    ws_info = [
        ws_id,
        "some_narrative",
        USER_ID,
        "2019-08-26T17:33:56+0000",
        7,
        "a",
        "r",
        "unlocked",
        {
            "cell_count": "1",
            "narrative_nice_name": "Test Exporting",
            "searchtags": "narrative",
            "is_temporary": "false",
            "narrative": "1",
        },
    ]
    user_map = {USER_ID: "Some User"}

    set_up_ok_mocks(
        requests_mock,
        ref_to_file=ref_to_file,
        ref_to_info=ref_to_info,
        ws_info=ws_info,
        user_map=user_map,
        ws_obj_info_file="data/43666/objects-43666.json",
    )

    exporter = NarrativeExporter(config, USER_ID, TOKEN)
    static_path = exporter.export_narrative(
        NarrativeRef({"wsid": ws_id, "objid": 1, "ver": 21}), scratch_dir
    )
    assert static_path == os.path.join(scratch_dir, "narrative.html")
