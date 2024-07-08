"""Tests for the StaticNarrativeCreator class."""

from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture
from pytest_mock.plugin import _mocker
from StaticNarrative.creator import StaticNarrativeCreator
from StaticNarrative.narrative_ref import NarrativeRef


@pytest.fixture()
def creator(config: Any, token: str) -> StaticNarrativeCreator:
    """Static Narrative Creator instance."""
    return StaticNarrativeCreator(config, token)


@pytest.mark.parametrize(
    "params",
    [
        [None, "token"],
        [{}, "token"],
        [{"this": "that"}, "token"],
        [{"workspace_url": "this"}, None],
        [{"workspace_url": "this"}, ""],
    ],
)
def test_init_invalid_init(
    params: list,
) -> None:
    """Ensure that invalid configs or tokens generate an error."""
    with pytest.raises(
        RuntimeError,
        match="Workspace URL and a token required to initialise the StaticNarrativeCreator.",
    ):
        StaticNarrativeCreator(*params)


def test_create_static_narrative(
    creator: StaticNarrativeCreator, mocker: Callable[..., Generator[MockerFixture, None, None]]
):
    mocker.patch.object(creator, "check_permissions")
    mocker.patch.object(creator, "export_narrative", return_value=Path("/tmp/static_narrative"))
    mocker.patch.object(
        creator, "upload_and_save", return_value="https://static.example.com/narrative"
    )

    params = {"narrative_ref": "12345/1/1", "user_id": "testuser"}

    result = creator.create_static_narrative(params)
    assert result["static_narrative_url"] == "https://static.example.com/narrative"


def test_export_narrative_fail_dir_issue(
    creator: StaticNarrativeCreator, tmp_path: Path, narr_ref: NarrativeRef, fake_user: str
) -> None:
    """Test the case where the static narrative base dir cannot be created."""
    scratch_dir = tmp_path / "output"
    scratch_dir.mkdir(mode=555)
    # oh no! the scratch directory has been misconfigured!
    creator.config["scratch"] = str(scratch_dir)

    with pytest.raises(RuntimeError, match="Could not create static narrative directory"):
        creator.export_narrative(narr_ref, fake_user)


def test_get_narrative_id_from_workspace(
    monkeypatch: pytest.MonkeyPatch, creator: StaticNarrativeCreator
):
    # patch the ws client to return valid(-ish) KBase obj info for a KBaseNarrative
    monkeypatch.setattr(
        "installed_clients.WorkspaceClient.Workspace.list_objects",
        lambda _x, _y: [[1, None, None, None, 1, None, 12345]],
    )

    narrative_id = creator.get_narrative_id_from_workspace(12345)
    assert narrative_id == "12345/1/1"


def test_get_narrative_id_from_workspace_not_found(
    monkeypatch: pytest.MonkeyPatch,
    creator: StaticNarrativeCreator,
):
    # patch the ws client to return valid(-ish) KBase obj info for a KBaseNarrative
    monkeypatch.setattr(
        "installed_clients.WorkspaceClient.Workspace.list_objects",
        lambda _x, _y: [],
    )

    with pytest.raises(
        ValueError, match="Workspace 12345 did not contain a KBaseNarrative.Narrative object."
    ):
        creator.get_narrative_id_from_workspace(12345)


def test_create_local_static_narrative(
    creator: StaticNarrativeCreator, mocker: Callable[..., Generator[MockerFixture, None, None]]
):
    mocker.patch.object(creator, "get_narrative_id_from_workspace", return_value="12345/1/1")
    mocker.patch.object(creator, "check_permissions")
    mocker.patch.object(creator, "export_narrative", return_value="/tmp/static_narrative")

    creator.create_local_static_narrative(12345, "testuser", "")
    creator.check_permissions.assert_called_once()
    creator.export_narrative.assert_called_once()
