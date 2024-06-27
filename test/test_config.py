"""Tests for the config package."""

from unittest.mock import patch

import pytest
from StaticNarrative.config import generate_config


@pytest.fixture()
def mock_os_path_isabs():
    with patch("os.path.isabs") as mock_isabs:
        yield mock_isabs


@pytest.fixture()
def mock_os_path_isdir():
    with patch("os.path.isdir") as mock_isdir:
        yield mock_isdir


@pytest.fixture()
def mock_os_access():
    with patch("os.access") as mock_access:
        yield mock_access


@pytest.fixture()
def mock_os_path_abspath():
    with patch("os.path.abspath") as mock_abspath:
        yield mock_abspath


def test_generate_config_fail_empty_config() -> None:
    with pytest.raises(RuntimeError, match="No config information found"):
        generate_config(None)


def test_generate_config_with_valid_config(
    mock_os_path_isabs, mock_os_path_isdir, mock_os_access, mock_os_path_abspath
) -> None:
    mock_os_path_isabs.side_effect = lambda x: x.startswith("/")
    mock_os_path_isdir.side_effect = lambda x: x.startswith("/")
    mock_os_access.side_effect = lambda x, y: True
    mock_os_path_abspath.side_effect = lambda x: f"/absolute/{x}"

    config = {
        "kbase-endpoint": "https://kbase.us/services",
        "static-file-root": "static-files",
        "scratch": "scratch-dir",
    }

    result = generate_config(config)

    expected_result = {
        "kbase-endpoint": "https://kbase.us/services",
        "workspace-url": "https://kbase.us/services/ws",
        "srv-wiz-url": "https://kbase.us/services/service_wizard",
        "auth-url": "https://kbase.us/services/auth",
        "nms-url": "https://kbase.us/services/narrative_method_store/rpc",
        "nms-image-url": "https://kbase.us/services/narrative_method_store/",
        "assets-base-url": "https://kbase.us/ui-assets",
        "static-file-root": "/absolute/static-files",
        "scratch": "/absolute/scratch-dir",
    }

    assert result == expected_result


def test_generate_config_fail_missing_kbase_endpoint() -> None:
    """Missing one of those required directories."""
    config = {"scratch": "blah", "static-file-root": "blahblah"}
    err_msg = "Missing required config values: kbase-endpoint"
    with pytest.raises(RuntimeError, match=err_msg):
        generate_config(config)


def test_generate_config_fail_unpopulated_kbase_endpoint() -> None:
    """KBase endpoint not populated."""
    config = {
        "kbase-endpoint": "{{ kbase_endpoint }}",
        "scratch": "this",
        "static-file-root": "that",
    }
    with pytest.raises(RuntimeError, match="Config file has not been populated correctly"):
        generate_config(config)


@pytest.mark.parametrize("to_test", ["scratch", "static-file-root"])
def test_generate_config_fail_missing_dir(to_test: str) -> None:
    """Missing one of those required directories."""
    config = {"kbase-endpoint": "https://some.url/whatever", to_test: "some_directory"}
    err_msg = "Missing required config values: "
    if to_test == "scratch":
        err_msg += "static-file-root"
    else:
        err_msg += "scratch"
    with pytest.raises(RuntimeError, match=err_msg):
        generate_config(config)


def test_generate_config_fail_missing_dirs() -> None:
    """Missing both required directories."""
    config = {"kbase-endpoint": "https://some.url/whatever"}
    err_msg = "Missing required config values: scratch, static-file-root"
    with pytest.raises(RuntimeError, match=err_msg):
        generate_config(config)


def test_generate_config_with_relative_paths(
    mock_os_path_isabs, mock_os_path_isdir, mock_os_access, mock_os_path_abspath
):
    """Check the absolutification of paths."""
    mock_os_path_isabs.side_effect = lambda x: False
    mock_os_path_isdir.side_effect = lambda x: True
    mock_os_access.side_effect = lambda x, y: True
    mock_os_path_abspath.side_effect = lambda x: f"/absolute/{x}"

    config = {
        "kbase-endpoint": "https://kbase.us/services",
        "static-file-root": "static-files",
        "scratch": "scratch-dir",
    }

    result = generate_config(config)
    assert result["static-file-root"] == "/absolute/static-files"
    assert result["scratch"] == "/absolute/scratch-dir"


def test_generate_config_fail_non_directory_static_file_root(
    mock_os_path_isabs, mock_os_path_isdir
):
    """Check that an error is thrown if static-file-root is not a directory.

    Note that static-file-root is checked first.
    """
    mock_os_path_isabs.side_effect = lambda x: True
    mock_os_path_isdir.side_effect = lambda x: False

    config = {
        "kbase-endpoint": "https://kbase.us/services",
        "static-file-root": "static-files",
        "scratch": "scratch-dir",
    }
    with pytest.raises(RuntimeError, match="static-file-root: static-files is not a directory"):
        generate_config(config)


def test_generate_config_fail_non_writable_scratch(
    mock_os_path_isabs, mock_os_path_isdir, mock_os_access
):
    """Check that an error is thrown if scratch is not writable."""
    mock_os_path_isabs.side_effect = lambda x: True
    mock_os_path_isdir.side_effect = lambda x: True
    mock_os_access.side_effect = lambda x, y: False

    config = {
        "kbase-endpoint": "https://kbase.us/services",
        "static-file-root": "/static-files",
        "scratch": "/scratch-dir",
    }
    with pytest.raises(RuntimeError, match="Cannot write to directory /scratch-dir"):
        generate_config(config)
