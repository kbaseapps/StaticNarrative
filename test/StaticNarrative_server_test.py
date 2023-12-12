"""Tests for the Static Narrative server module."""
from test.mocks import set_up_ok_mocks
from typing import Any

import pytest
from StaticNarrative.StaticNarrativeImpl import StaticNarrative

USER_ID = "some_user"


def test_status(
    static_narrative_service: StaticNarrative, context: dict[str, Any]
) -> None:
    status = static_narrative_service.status(context)[0]
    assert status == {
        "state": "OK",
        "message": "",
        "version": static_narrative_service.VERSION,
        "git_url": static_narrative_service.GIT_URL,
        "git_commit_hash": static_narrative_service.GIT_COMMIT_HASH,
    }
    assert status["version"] is not None
    assert status["git_url"] is not None
    assert status["git_commit_hash"] is not None


def test_create_static_narrative_ok_unit(
    static_narrative_service: StaticNarrative, context: dict[str, Any], requests_mock
) -> None:
    """Runs through the create process with a number of narratives."""
    ref_to_file = {}
    # 1. Add ref -> file for narratives
    narr_refs = [
        "5846/1/19",
        "25022/1/114",
        "30530/107/25",
        "40800/178/1",
        "43666/1/18",
        "43666/1/21",
        "54980/144/1",
        "47123/1/28",
    ]
    ws_to_reports = {
        "5846": [],
        "25022": [
            "25022/4",
            "25022/6",
            "25022/8",
            "25022/9",
            "25022/11",
            "25022/12",
            "25022/13",
            "25022/19",
            "25022/20",
            "25022/31",
            "25022/34",
        ],
        "30530": [
            "30462/16",
            "30462/73",
            "30462/80",
            "30462/82",
            "30462/96",
            "30462/105",
            "30462/106",
            "30530/108",
            "30530/109",
            "30530/110",
            "30530/111",
            "30530/112",
            "30530/113",
            "30530/114",
        ],
        "40800": [
            "40589/17/2",
            "40589/22/3",
            "40589/30/2",
            "40589/31",
            "40589/32",
            "40589/43",
            "40589/44",
            "40589/175",
        ],
        "43666": ["43666/3", "43666/7"],
        "47123": ["47123/4", "47123/5", "47123/6", "47123/7", "47123/8", "47123/9"],
        "54980": ["24065/141", "24065/143"],
    }
    for ref in narr_refs:
        ws_id = ref.split("/")[0]
        ref_dots = ref.replace("/", ".")
        ref_to_file[ref] = f"data/{ws_id}/narrative-{ref_dots}.json"
    for ws_id in ws_to_reports:
        for report_ref in ws_to_reports[ws_id]:
            if len(report_ref.split("/")) == 2:
                report_ref = report_ref + "/1"
            ref_dots = report_ref.replace("/", ".")
            ref_to_file[report_ref] = f"data/{ws_id}/report-{ref_dots}.json"
    for narr_ref in narr_refs:
        ws_id = int(narr_ref.split("/")[0])
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
        ws_perms = {ws_id: {USER_ID: "a", "*": "r", "some_other_user": "w"}}
        user_map = {USER_ID: "Some User", "some_other_user": "Some Other User"}
        set_up_ok_mocks(
            requests_mock,
            ref_to_file=ref_to_file,
            ref_to_info={},
            ws_info=ws_info,
            ws_perms=ws_perms,
            user_map=user_map,
            ws_obj_info_file=f"data/{ws_id}/objects-{ws_id}.json",
        )
        output = static_narrative_service.create_static_narrative(
            context, {"narrative_ref": narr_ref}
        )[0]
        assert output["static_narrative_url"] == f"/{ws_id}/{narr_ref.split('/')[-1]}/"


def test_create_static_narrative_no_auth() -> None:
    """Test case where user isn't logged in, or just no auth token passed."""


def test_create_static_narrative_user_not_admin(
    static_narrative_service: StaticNarrative, context: dict[str, Any], requests_mock
) -> None:
    """Test case where user doesn't have admin rights on the workspace."""
    ws_id = 12345
    set_up_ok_mocks(
        requests_mock,
        ws_perms={ws_id: {USER_ID: "n"}},
        user_map={USER_ID: "Some User"},
    )
    with pytest.raises(
        PermissionError,
        match=f"User {USER_ID} does not have admin rights on workspace {ws_id}",
    ):
        static_narrative_service.create_static_narrative(
            context, {"narrative_ref": f"{ws_id}/1/1"}
        )


def test_create_static_narrative_not_public(
    static_narrative_service: StaticNarrative, context: dict[str, Any], requests_mock
) -> None:
    """Test case where Narative isn't public."""
    ws_perms = {123: {USER_ID: "a", "*": "n"}, 456: {USER_ID: "a"}}
    set_up_ok_mocks(requests_mock, ws_perms=ws_perms, user_map={USER_ID: "Some User"})
    for ws_id in ws_perms:
        with pytest.raises(
            PermissionError,
            match=f"Workspace {ws_id} must be publicly readable to make a Static Narrative",
        ):
            static_narrative_service.create_static_narrative(
                context, {"narrative_ref": f"{ws_id}/1/1"}
            )


def test_create_static_narrative_bad() -> None:
    """Test case with a badly formed Narrative object."""
    # TODO!


def test_get_static_info_ok(
    static_narrative_service: StaticNarrative, context: dict[str, Any], requests_mock
) -> None:
    ws_id = 5
    ws_name = "fake_ws"
    ts_iso = "2019-10-24T21:51:17+0000"
    ws_meta = {
        "cell_count": "1",
        "narrative_nice_name": "Tester",
        "searchtags": "narrative",
        "is_temporary": "false",
        "narrative": "1",
        "static_narrative_ver": "1",
        "static_narrative_saved": "1573170933432",
        "static_narrative": "/5/1",
    }
    ref_to_file = {}
    ref_to_info = {
        "5/1/1": [
            1,
            "fake_narr",
            "KBaseNarrative.Narrative-4.0",
            ts_iso,
            1,
            USER_ID,
            ws_id,
            ws_name,
            "an_md5",
            12345,
            None,
        ]
    }
    ws_info = [5, ws_name, USER_ID, ts_iso, 1, "a", "r", "unlocked", ws_meta]
    set_up_ok_mocks(
        requests_mock, ref_to_file=ref_to_file, ref_to_info=ref_to_info, ws_info=ws_info
    )
    info = static_narrative_service.get_static_narrative_info(
        context, {"ws_id": ws_id}
    )[0]
    std_info = {
        "ws_id": ws_id,
        "version": 1,
        "narrative_id": 1,
        "url": "/5/1",
        "static_saved": 1573170933432,
        "narr_saved": 1571953877000,
    }
    assert info == std_info


def test_list_static_narratives(
    static_narrative_service: StaticNarrative, context: dict[str, Any]
) -> None:
    """TODO: better testing. set up specific files, narratives, maybe run all the things first.
    TODO: deeper unit testing?
    """
    narrs = static_narrative_service.list_static_narratives(context)[0]
    print(narrs)
