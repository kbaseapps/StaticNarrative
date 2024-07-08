"""Tests for the config package."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from StaticNarrative.config import generate_config


def absolutify(self: Path) -> Path:
    """Generate an absolute version of a path."""
    return Path("/absolute") / self


@pytest.fixture()
def mock_os_access() -> Generator[MagicMock, Any, None]:
    with patch("os.access") as mock_access:
        yield mock_access


def test_generate_config_fail_empty_config() -> None:
    with pytest.raises(RuntimeError, match="No config information found"):
        generate_config(None)


def test_generate_config_with_valid_config(
    monkeypatch: pytest.MonkeyPatch,
    mock_os_access: MagicMock,
) -> None:
    mock_os_access.side_effect = lambda x, y: True

    def starts_with_slash(self) -> bool:
        """Fake function to replace is_absolute and is_dir."""
        return str(self).startswith("/")

    monkeypatch.setattr(Path, "is_absolute", starts_with_slash)
    monkeypatch.setattr(Path, "is_dir", starts_with_slash)
    monkeypatch.setattr(Path, "resolve", absolutify)
    config = {
        "kbase_endpoint": "https://kbase.us/services",
        "static_file_root": "static-files",
        "scratch": "scratch-dir",
    }

    result = generate_config(config)

    expected_result = {
        "kbase_endpoint": "https://kbase.us/services",
        "workspace_url": "https://kbase.us/services/ws",
        "srv_wiz_url": "https://kbase.us/services/service_wizard",
        "auth_url": "https://kbase.us/services/auth",
        "nms_url": "https://kbase.us/services/narrative_method_store/rpc",
        "nms_image_url": "https://kbase.us/services/narrative_method_store/",
        "assets_base_url": "https://kbase.us/ui-assets",
        "static_file_root": "/absolute/static-files",
        "scratch": "/absolute/scratch-dir",
    }

    assert result == expected_result


def test_generate_config_fail_missing_kbase_endpoint() -> None:
    """Missing one of those required directories."""
    config = {"scratch": "blah", "static_file_root": "blahblah"}
    err_msg = "Missing required config values: kbase_endpoint"
    with pytest.raises(RuntimeError, match=err_msg):
        generate_config(config)


def test_generate_config_fail_unpopulated_kbase_endpoint() -> None:
    """KBase endpoint not populated."""
    config = {
        "kbase_endpoint": "{{ kbase_endpoint }}",
        "scratch": "this",
        "static_file_root": "that",
    }
    with pytest.raises(RuntimeError, match="Config file has not been populated correctly"):
        generate_config(config)


@pytest.mark.parametrize("to_test", ["scratch", "static_file_root"])
def test_generate_config_fail_missing_dir(to_test: str) -> None:
    """Missing one of those required directories."""
    config = {"kbase_endpoint": "https://some.url/whatever", to_test: "some_directory"}
    err_msg = "Missing required config values: "
    if to_test == "scratch":
        err_msg += "static_file_root"
    else:
        err_msg += "scratch"
    with pytest.raises(RuntimeError, match=err_msg):
        generate_config(config)


def test_generate_config_fail_missing_dirs() -> None:
    """Missing both required directories."""
    config = {"kbase_endpoint": "https://some.url/whatever"}
    err_msg = "Missing required config values: scratch, static_file_root"
    with pytest.raises(RuntimeError, match=err_msg):
        generate_config(config)


def test_generate_config_with_relative_paths(
    monkeypatch: pytest.MonkeyPatch,
    mock_os_access: MagicMock,
) -> None:
    """Check the absolutification of paths."""
    mock_os_access.side_effect = lambda x, y: True

    monkeypatch.setattr(Path, "is_absolute", lambda _: False)
    monkeypatch.setattr(Path, "is_dir", lambda _: True)
    monkeypatch.setattr(Path, "resolve", absolutify)

    config = {
        "kbase_endpoint": "https://kbase.us/services",
        "static_file_root": "static-files",
        "scratch": "scratch-dir",
    }

    result = generate_config(config)
    assert result["static_file_root"] == "/absolute/static-files"
    assert result["scratch"] == "/absolute/scratch-dir"


def test_generate_config_fail_non_directory_static_file_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that an error is thrown if static_file_root is not a directory.

    Note that static_file_root is checked first.
    """
    monkeypatch.setattr(Path, "is_absolute", lambda _: True)
    monkeypatch.setattr(Path, "is_dir", lambda _: False)

    config = {
        "kbase_endpoint": "https://kbase.us/services",
        "static_file_root": "static-files",
        "scratch": "scratch-dir",
    }
    with pytest.raises(RuntimeError, match="static_file_root: static-files is not a directory"):
        generate_config(config)


def test_generate_config_fail_non_writable_scratch(
    mock_os_access: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that an error is thrown if scratch is not writable."""
    mock_os_access.side_effect = lambda x, y: False
    monkeypatch.setattr(Path, "is_absolute", lambda _: True)
    monkeypatch.setattr(Path, "is_dir", lambda _: True)

    config = {
        "kbase_endpoint": "https://kbase.us/services",
        "static_file_root": "/static-files",
        "scratch": "/scratch-dir",
    }
    with pytest.raises(RuntimeError, match="Cannot write to directory /scratch-dir"):
        generate_config(config)
