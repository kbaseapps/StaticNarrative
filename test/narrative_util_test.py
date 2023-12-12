"""Tests for the narrative_util module."""
import time
from test.mocks import mock_ws_bad, set_up_ok_mocks

import pytest
from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.exceptions import WorkspaceError
from StaticNarrative.narrative.narrative_util import (
    _validate_narr_type,
    get_static_info,
    read_narrative,
    save_narrative_url,
    verify_admin_privilege,
    verify_public_narrative,
)
from StaticNarrative.narrative_ref import NarrativeRef

USER_ID = "some_user"
TOKEN = "some_token"  # noqa: S105
REF = NarrativeRef.parse("1/2/3")


def test_read_narrative_ok(workspace_url: str, requests_mock) -> None:
    ref = "43666/1/18"
    ref_to_file = {ref: "data/43666/narrative-43666.1.18.json"}
    set_up_ok_mocks(requests_mock, ref_to_file=ref_to_file)
    nar = read_narrative(
        NarrativeRef.parse("43666/1/18"),
        Workspace(url=workspace_url, token=TOKEN),
    )
    # spot check that it's loaded and formatted
    assert nar is not None
    assert "cells" in nar
    assert len(nar["cells"]) == 9


def test_read_narrative_bad_client(workspace_url: str, requests_mock) -> None:
    ws_id = 908
    mock_ws_bad(requests_mock, "Can't fetch object")
    with pytest.raises(WorkspaceError, match=f"{ws_id}.+Can't fetch object"):
        read_narrative(
            NarrativeRef.parse("908/1/1"),
            Workspace(url=workspace_url, token=TOKEN),
        )


def test_read_narrative_not_narrative(workspace_url: str, requests_mock) -> None:
    ref = "43666/3/1"
    ref_to_file = {ref: "data/43666/report-43666.3.1.json"}
    set_up_ok_mocks(requests_mock, ref_to_file=ref_to_file)
    with pytest.raises(
        ValueError,
        match=f"Expected a Narrative object with reference {ref}, got a KBaseReport.Report-3.0",
    ):
        read_narrative(
            NarrativeRef.parse(ref),
            Workspace(url=workspace_url, token=TOKEN),
        )


@pytest.mark.parametrize(
    "type_string", ["KBaseNarrative.Narrative-1.0", "KBaseNarrative.Narrative-4.0"]
)
def test_validate_narr_type_good_types(type_string: str) -> None:
    assert _validate_narr_type(type_string, REF) is None


@pytest.mark.parametrize(
    "type_string",
    [
        "SomeObject.Name",
        "kbasenarrative.Narrative-1.0",
        "KBaseNarrative.Narrative-1.0.0",
    ],
)
def test_validate_narr_type_bad_types(type_string: str) -> None:
    with pytest.raises(
        ValueError,
        match=f"Expected a Narrative object with reference {REF!s}, got a",
    ):
        _validate_narr_type(type_string, REF)


@pytest.mark.parametrize("type_string", [5, str, {"lol": "no"}, ["wat"], None])
def test_validate_narr_type(
    type_string: type[str] | dict[str, str] | list[str] | None
) -> None:
    with pytest.raises(ValueError, match="The type string must be a string"):
        _validate_narr_type(type_string, REF)


def test_save_narrative_url() -> None:
    pass


def test_save_narrative_url_bad(workspace_url: str, requests_mock) -> None:
    mock_ws_bad(requests_mock, "Failed to alter metadata")
    ws_id = 234
    with pytest.raises(WorkspaceError, match=f"{ws_id}.+Failed to alter metadata"):
        save_narrative_url(
            workspace_url,
            TOKEN,
            NarrativeRef.parse("234/1/2"),
            "/234/1",
        )


@pytest.mark.parametrize("ws_id", ["foo", "onetwo", {"no": "way"}, ["nope"], None, str])
def test_get_static_info_bad(
    ws_id: dict[str, str] | list[str] | type[str] | str | None
) -> None:
    with pytest.raises(
        ValueError, match="The parameter ws_id must be an integer, not "
    ):
        get_static_info("someurl", "some_token", ws_id)


def test_get_static_info_ok(workspace_url: str, requests_mock) -> None:
    ws_id1 = 123
    ws_id2 = 456
    save_time = str(int(time.time() * 1000))
    ws_ts = "2019-08-26T17:33:56+0000"
    ws_ts_epoch = 1566840836000
    obj_info = [
        1,
        "fake_narr",
        "KBaseNarrative.Narrative-4.0",
        ws_ts,
        1,
        "some_user",
        5,
        "fake_ws",
        "an_md5",
        12345,
        None,
    ]
    ref_to_info = {f"{ws_id1}/1/1": obj_info, f"{ws_id2}/1/1": obj_info}
    ws_info_map = {
        ws_id1: [
            ws_id1,
            "some_util_test_narrative",
            USER_ID,
            ws_ts,
            7,
            "a",
            "r",
            "unlocked",
            {
                "cell_count": "1",
                "narrative_nice_name": "Test Exporting 1",
                "searchtags": "narrative",
                "is_temporary": "false",
                "narrative": "1",
            },
        ],
        ws_id2: [
            ws_id2,
            "some_other_util_test_narrative",
            USER_ID,
            ws_ts,
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
                "static_narrative_ver": "1",
                "static_narrative_saved": save_time,
                "static_narrative": f"/{ws_id2}/1",
            },
        ],
    }
    set_up_ok_mocks(requests_mock, ref_to_info=ref_to_info, ws_info=ws_info_map[ws_id1])
    info = get_static_info(workspace_url, TOKEN, ws_id1)
    assert info == {}

    set_up_ok_mocks(requests_mock, ref_to_info=ref_to_info, ws_info=ws_info_map[ws_id2])
    info = get_static_info(workspace_url, TOKEN, ws_id2)
    assert info == {
        "ws_id": ws_id2,
        "narrative_id": 1,
        "version": 1,
        "url": f"/{ws_id2}/1",
        "static_saved": int(save_time),
        "narr_saved": ws_ts_epoch,
    }


def test_static_info_ws_err(workspace_url: str, requests_mock) -> None:
    mock_ws_bad(requests_mock, "Workspace not found")
    with pytest.raises(WorkspaceError, match="123"):
        get_static_info(workspace_url, TOKEN, 123)


def test_verify_admin_privs_ok(workspace_url: str, requests_mock) -> None:
    ws_ids_ok = {123: {USER_ID: "a"}, "1123": {USER_ID: "a"}}
    set_up_ok_mocks(requests_mock, ws_perms=ws_ids_ok)
    for ws_id in ws_ids_ok:
        # verify_admin_privilege throws an error if the user doesn't have privs,
        # so we just check that each function completes successfully.
        verify_admin_privilege(workspace_url, USER_ID, TOKEN, ws_id)


def test_verify_admin_privs_fail(workspace_url: str, requests_mock) -> None:
    ws_no_privs = {
        123: {USER_ID: "n"},
        456: {USER_ID: "w"},
        789: {USER_ID: "r"},
        234: {"some_other_user": "a", "*": "r"},
    }
    set_up_ok_mocks(requests_mock, ws_perms=ws_no_privs)
    for ws_id in ws_no_privs:
        with pytest.raises(
            PermissionError,
            match=f"User {USER_ID} does not have admin rights on workspace {ws_id}",
        ):
            verify_admin_privilege(workspace_url, USER_ID, TOKEN, ws_id)


def test_verify_admin_privs_bad_client(workspace_url: str, requests_mock) -> None:
    mock_ws_bad(requests_mock, "Can't reach workspace")
    ws_id = 5
    with pytest.raises(WorkspaceError, match=f"{ws_id}.+Can't reach workspace"):
        verify_admin_privilege(workspace_url, USER_ID, TOKEN, ws_id)


def test_verify_public_narrative_ok(workspace_url: str, requests_mock) -> None:
    # all kinda stupid, but valid.
    ws_perms = {
        123: {USER_ID: "a", "*": "r"},
        456: {USER_ID: "n", "*": "w"},
        "789": {USER_ID: "r", "*": "a"},
    }
    set_up_ok_mocks(requests_mock, ws_perms=ws_perms)

    # verify_public_narrative throws an error so just ensure that the
    # functions execute without issue.
    for ws_id in ws_perms:
        verify_public_narrative(workspace_url, ws_id)


def test_verify_public_narrative_fail(workspace_url: str, requests_mock) -> None:
    ws_no_privs = {
        123: {USER_ID: "n"},
        "456": {USER_ID: "a"},
        789: {USER_ID: "w"},
    }
    set_up_ok_mocks(requests_mock, ws_perms=ws_no_privs)
    for ws_id in ws_no_privs:
        with pytest.raises(
            PermissionError,
            match=f"Workspace {ws_id} must be publicly readable to make a Static Narrative",
        ):
            verify_public_narrative(workspace_url, ws_id)


def test_verify_public_privs_bad_client(workspace_url: str, requests_mock) -> None:
    mock_ws_bad(requests_mock, "Can't reach workspace")
    ws_id = 666
    with pytest.raises(WorkspaceError, match=f"{ws_id}.+Can't reach workspace"):
        verify_public_narrative(workspace_url, ws_id)
