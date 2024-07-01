"""Tests of the exporter module."""

import os
import shutil
from pathlib import Path
from unittest import mock

import pytest
from nbconvert import HTMLExporter
from StaticNarrative.exporter.dynamic_service_client import DynamicServiceClient
from StaticNarrative.exporter.exporter import OUTPUT_HTML_FILE, NarrativeExporter
from StaticNarrative.narrative_ref import NarrativeRef

from test.mocks import set_up_ok_mocks

USER_ID = "some_user"
TOKEN = "some_token"  # noqa: S105


def check_files_identical(file1_path: str | Path, file2_path: str | Path) -> None:
    """Check whether two files are identical.

    :param file1_path: full path to file 1
    :type file1_path: str
    :param file2_path: full path to file 2
    :type file2_path: str
    """
    with open(file1_path) as file1:
        file1_contents = file1.read()

    with open(file2_path) as file2:
        file2_contents = file2.read()

    if file2_contents != file1_contents:
        shutil.copyfile(file2_path, str(file1_path) + "-alt")
    assert file1_contents == file2_contents, "The files do not have identical contents."


WORKSPACE_IDS = [
    # "5846/1/19",  # deleted
    "25022/1/114",  # not identical due to UUIDs
    # "30530/107/25",  # narrative deleted
    # "40800/178/1",  # deleted
    "43666/1/18",
    "43666/1/21",
    "47123/1/24",
    "47123/1/28",
    # "54980/144/1",  # no access
    "67395/1003/83",
    "69666/1050/10",
    # 86723,
]


@pytest.mark.parametrize(
    "ws_id",
    WORKSPACE_IDS,
)
@pytest.mark.vcr()
def test_narrative_exporter_set_api_vs_gsn(
    config: dict[str, str], token: str, ws_id: str, tmpdir: Path
) -> None:
    """Ensure that the narrative exporter exports the appropriate narrative."""
    narr_ref = NarrativeRef.parse(ws_id)
    narrative_exporter = NarrativeExporter(config, USER_ID, token)
    original_function = narrative_exporter._build_exporter  # noqa: SLF001

    set_api_dir = tmpdir / "set_api"
    gsn_dir = tmpdir / "gsn"

    os.makedirs(set_api_dir, exist_ok=True)
    os.makedirs(gsn_dir, exist_ok=True)

    def side_effect(*args, **kwargs) -> HTMLExporter:
        """Patch the html exporter to remove the `uuid` function which adds randomness to the templates."""
        html_exporter = original_function(*args, **kwargs)
        html_exporter.environment.globals["uuid4"] = lambda: "uuid"
        return html_exporter

    with mock.patch.object(narrative_exporter, "_build_exporter", side_effect=side_effect):
        # run the exporter using the SetAPI client
        narrative_exporter.export_narrative(narr_ref, str(set_api_dir))

        # remove the SetAPI client and rerun the exporter
        narrative_exporter.set_api_client = None
        narrative_exporter.export_narrative(narr_ref, str(gsn_dir))

        # compare contents
        for file in ["data.json", OUTPUT_HTML_FILE]:
            check_files_identical(
                set_api_dir / file,
                gsn_dir / file,
            )


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
    assert isinstance(exporter.set_api_client, DynamicServiceClient)
    static_path = exporter.export_narrative(
        NarrativeRef({"wsid": ws_id, "objid": 1, "ver": 21}), scratch_dir
    )
    assert static_path == os.path.join(scratch_dir, OUTPUT_HTML_FILE)
