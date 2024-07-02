"""Tests for the processor util module."""

from copy import deepcopy
from typing import Any
from unittest.mock import create_autospec

import pytest
from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.exporter.processor_util import (
    build_report_view_data,
    get_authors,
    get_created_objects_from_report,
)
from traitlets.config import Config

from test.mocks import set_up_ok_mocks


def test_report_with_none_direct_link_index_and_truthy_html_links() -> None:
    """Test for error reported in Jira ticket PUBLIC-1411.

    Tests the case where a report contains a direct_html_link_index key with a value of None
    and a truthy html_links entry. This caused a None vs. int comparison error in an earlier
    version of the code.
    """
    ws = create_autospec(Workspace, spec_set=True, instance=True)

    ws.get_objects2.return_value = {
        "data": [
            {
                "data": {
                    "direct_html_link_index": None,
                    "html_links": [{"name": "win32k.sys"}],
                }
            }
        ]
    }

    report_result = {"report_name": "I am report. Fear me", "report_ref": "1/2/3"}

    res = build_report_view_data(ws, {}, "https://spongebobfreenoods.com/", report_result)

    expected = {
        "objects": [],
        "summary": "",
        "summary_height": "500px",
        "html": {
            "height": "500px",
            "set_height": True,
            "links": [{"name": "win32k.sys"}],
            "paths": ["/api/v1/1/2/3/$/0/win32k.sys"],
            "link_idx": 0,
            "iframe_style": "max-height: 500px; height: 500px",
        },
    }

    assert res == expected

    ws.get_objects2.assert_called_once_with({"objects": [{"ref": "1/2/3"}]})


@pytest.mark.parametrize(
    "report_input",
    [
        None,
        "",
        12345,
        [],
        {},
        ["this", "that"],
        [["this"], ["that"]],
        {"this": "that", "the": "other"},
    ],
)
def test_build_report_invalid_input(ws_client: Workspace, report_input) -> None:
    """Ensure that invalid input to build_report... returns an empty dict."""
    assert build_report_view_data(ws_client, {}, "string", report_input) == {}


@pytest.mark.parametrize("report_ref", ["123/4/5", "67395/1066/1", "67395/2066/1"])
@pytest.mark.vcr()
def test_build_report_view_data_fail_no_report(ws_client: Workspace, report_ref: str) -> None:
    """Test for the case where a workspace report does not exist.

    123/4/5: workspace deleted
    67395/1066/1: report deleted
    67395/2066/1: obj does not exist
    """
    assert (
        build_report_view_data(
            ws_client, {}, "string", {"report_name": "my_report", "report_ref": report_ref}
        )
        == {}
    )


@pytest.mark.parametrize("report", [{}, {"objects_created": []}])
def test_get_created_objects_from_report_no_objects(
    ws_client: Workspace, report: dict[str, list[Any]]
) -> None:
    """Test that an empty list is returned if there are no objects created."""
    assert (
        get_created_objects_from_report(
            ws_client,
            {},
            "some_host",
            report,
        )
        == []
    )


INDEXED_DATA = {
    "67395/24/1": {
        "object_info": [
            24,
            "assy00014",
            "KBaseGenomeAnnotations.Assembly-6.0",
            "2022-04-14T13:26:52+0000",
            1,
            "ialarmedalien",
            67395,
            "ialarmedalien:narrative_1649942812539",
            "b875f0cb383d3996e57614d39240e486",
            795,
            None,
        ],
    },
    "67395/26/1": {
        "object_info": [
            26,
            "assy00015",
            "KBaseGenomeAnnotations.Assembly-6.0",
            "2022-04-14T13:26:52+0000",
            1,
            "ialarmedalien",
            67395,
            "ialarmedalien:narrative_1649942812539",
            "41c146af80cff5a7d688c812ddf758b9",
            795,
            None,
        ],
    },
    "67395/1004/1": {
        "object_info": [
            1004,
            "_Chrysanthemum_coronarium__phytoplasma",
            "KBaseGenomes.Genome-17.0",
            "2023-03-10T22:30:44+0000",
            1,
            "ialarmedalien",
            67395,
            "ialarmedalien:narrative_1649942812539",
            "035f385d35a9cf8c7889e5728c5035ef",
            2505433,
            None,
        ]
    },
    "67395/1066/1": None,  # deleted
    "67395/2066/1": None,  # does not exist
}


@pytest.mark.parametrize(
    "params",
    [
        # all objects in indexed data
        pytest.param(INDEXED_DATA, id="all_objects"),
        # some objects in indexed data
        pytest.param(
            {
                "67395/26/1": INDEXED_DATA["67395/26/1"],
                "67395/1004/1": INDEXED_DATA["67395/1004/1"],
            },
            id="some_objects",
        ),
        # no objects in indexed data
        pytest.param({}, id="no_objects"),
    ],
)
@pytest.mark.vcr()
def test_get_created_objects_from_report(ws_client: Workspace, params: dict[str, Any]) -> None:
    """Test retrieval of created objects from a report."""
    host = "https://example.com"
    indexed_data = deepcopy(params)
    output = get_created_objects_from_report(
        ws_client,
        indexed_data,
        host,
        {
            "objects_created": [
                {"ref": "67395/24/1", "description": "obj 1"},
                {"ref": "67395/26/1", "description": ""},
                {"ref": "67395/1066/1", "description": "a deleted report"},
                {"ref": "67395/2066/1", "description": "a non-existent object"},
                {"ref": "67395/1004/1", "description": "something different"},
            ]
        },
    )

    assert output == [
        {
            "upa": "67395/24/1",
            "description": "obj 1",
            "name": "assy00014",
            "type": "Assembly",
            "link": f"{host}/#dataview/67395/24/1",
        },
        {
            "upa": "67395/26/1",
            "description": "",
            "name": "assy00015",
            "type": "Assembly",
            "link": f"{host}/#dataview/67395/26/1",
        },
        {
            "upa": "67395/1004/1",
            "description": "something different",
            "name": "_Chrysanthemum_coronarium__phytoplasma",
            "type": "Genome",
            "link": f"{host}/#dataview/67395/1004/1",
        },
    ]
    assert indexed_data == INDEXED_DATA


USERS = ["owner", "user_1", "user_2", "user_3"]
NAMES = ["The Wizard of Oz", "<insert name here>", "Me; Myself; & I", "Occam's Razor"]
HTML_NAMES = [
    "The Wizard of Oz",
    "&lt;insert name here&gt;",
    "Me; Myself; &amp; I",
    "Occam's Razor",
]

DISPLAY_NAMES = dict(zip(USERS, NAMES, strict=True))

AUTH_SERVER_OK = [
    {"id": USERS[ix], "name": HTML_NAMES[ix], "path": f"profile_page_path/{item}"}
    for ix, item in enumerate(USERS)
]

NO_AUTH_SERVER = [{"id": item, "name": item, "path": f"profile_page_path/{item}"} for item in USERS]


@pytest.mark.parametrize("auth_server_available", [True, False])
@pytest.mark.parametrize("wsid", [54321, 54322, 54333, 54444])
def test_get_authors_auth_server_available(
    ws_client: Workspace,
    fake_token: str,
    config: dict[str, Any],
    wsid: int,
    requests_mock,
    auth_server_available: bool,
) -> None:
    """Check the output of the get_authors command with a range of inputs and with or without the auth server response."""
    workspace_get_permissions = {
        54321: {},
        54322: {
            USERS[0]: "a",
            "*": "r",
        },
        54333: {
            USERS[0]: "a",
            USERS[1]: "a",
            "*": "r",
        },
        54444: {
            USERS[0]: "a",
            "*": "r",
            USERS[1]: "a",
            USERS[2]: "w",
            USERS[3]: "r",
        },
    }

    set_up_ok_mocks(
        requests_mock,
        ws_info=[wsid, f"{USERS[0]}:narrative_12345", USERS[0]],
        ws_perms=workspace_get_permissions,
        user_map=DISPLAY_NAMES if auth_server_available else {},
    )

    conf = Config(
        profile_page_path="profile_page_path/", token=fake_token, auth_url=config["auth_url"]
    )

    output = get_authors(ws_client, conf, wsid)
    expected_output = NO_AUTH_SERVER
    if auth_server_available:
        expected_output = AUTH_SERVER_OK

    if wsid in [54321, 54322]:
        assert output == expected_output[:1]
    elif wsid == 54333:
        assert output == expected_output[:2]
    elif wsid == 54444:
        assert output == expected_output[:3]
