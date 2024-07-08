"""Tests for icon_utils."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import StaticNarrative.exporter.icon_util
from StaticNarrative.exporter.icon_util import (
    _load_icon_data,
    get_data_icon,
    get_icon,
)

from test import TEST_BASE_DIR

TEST_ICON_DATA_FILE = TEST_BASE_DIR / "data" / "icon_data.json"

# Sample JSON data for testing - this is identical to the
# contents of TEST_BASE_DIR / data / icon_data.json
sample_icon_data = {
    "methods": {"method": ["fa-cube"], "app": ["fa-cubes"]},
    "data": {
        "DEFAULT": ["fa-file-o"],
        "AssemblyInput": ["icon icon-reads"],
        "Assembly": ["fa-align-justify"],
    },
    "colors": ["#F44336", "#E91E63", "#9C27B0"],
    "color_mapping": {"AssemblyInput": "#F44336", "Assembly": "#920D58"},
}


@pytest.fixture()
def _sample_icon_data_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("StaticNarrative.exporter.icon_util.ICON_DATA_FILE", TEST_ICON_DATA_FILE)


@pytest.mark.usefixtures("_sample_icon_data_file")
def test_load_icon_data_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check that icon data loads correctly."""
    # Ensure ICON_DATA is None before loading
    monkeypatch.setattr("StaticNarrative.exporter.icon_util.ICON_DATA", None)

    assert StaticNarrative.exporter.icon_util.ICON_DATA is None

    _load_icon_data()

    # ensure that the sample icon data has been loaded.
    assert sample_icon_data == StaticNarrative.exporter.icon_util.ICON_DATA


def test_load_icon_data_file_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Icon file cannot be found."""
    icon_data_file = Path("/path/to/nonexistent.json")
    monkeypatch.setattr("StaticNarrative.exporter.icon_util.ICON_DATA_FILE", icon_data_file)

    with pytest.raises(FileNotFoundError, match=f"File {icon_data_file} not found."):
        _load_icon_data()


def test_load_icon_data_file_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Icon file is empty."""
    icon_data_file = tmp_path / "empty.json"
    icon_data_file.touch()
    monkeypatch.setattr("StaticNarrative.exporter.icon_util.ICON_DATA_FILE", icon_data_file)

    with pytest.raises(ValueError, match=f"File {icon_data_file} is not a valid JSON file."):
        _load_icon_data()


def test_load_icon_data_invalid_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Icon file is not valid JSON."""
    icon_data_file = tmp_path / "invalid.json"
    monkeypatch.setattr("StaticNarrative.exporter.icon_util.ICON_DATA_FILE", icon_data_file)
    with icon_data_file.open("w") as icon_file:
        icon_file.write("{invalid json}")

    with pytest.raises(ValueError, match=f"File {icon_data_file} is not a valid JSON file."):
        _load_icon_data()


def test_load_icon_data_empty_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Icon file is not valid JSON."""
    icon_data_file = tmp_path / "empty.json"
    monkeypatch.setattr("StaticNarrative.exporter.icon_util.ICON_DATA_FILE", icon_data_file)
    with icon_data_file.open("w") as icon_file:
        icon_file.write("{}")

    with pytest.raises(ValueError, match=f"No icon data found in {icon_data_file}."):
        _load_icon_data()


@pytest.mark.usefixtures("_sample_icon_data_file")
def test_get_data_icon_default() -> None:
    """Get the data icon for an unknown data type."""
    result = get_data_icon("UnknownType")
    expected = {
        "icon": ["fa-file-o"],
        "color": "#F44336",
        "shape": "circle",
    }
    assert result == expected


@pytest.mark.usefixtures("_sample_icon_data_file")
def test_get_data_icon_specific_type() -> None:
    """Get the data icon for an Assembly."""
    result = get_data_icon("Assembly")
    expected = {
        "icon": "fa-align-justify",
        "color": "#920D58",
        "shape": "circle",
    }
    assert result == expected


@pytest.mark.usefixtures("_sample_icon_data_file")
def test_get_icon_data_type() -> None:
    """Get the icon for a data type."""
    config = MagicMock()
    metadata = {"type": "data", "dataCell": {"objectInfo": {"typeName": "Assembly"}}}

    result = get_icon(config, metadata)
    expected = {"type": "class", "icon": "fa-align-justify", "color": "#920D58", "shape": "circle"}
    assert result == expected


@pytest.mark.usefixtures("_sample_icon_data_file")
def test_get_icon_output_type() -> None:
    """Get the icon for an output type."""
    config = MagicMock()
    metadata = {"type": "output"}

    result = get_icon(config, metadata)
    expected = {"type": "class", "icon": "fa-arrow-right", "color": "silver", "shape": "square"}
    assert result == expected


@pytest.mark.usefixtures("_sample_icon_data_file")
def test_get_icon_app_type() -> None:
    """Get the icon for an app with an image icon."""
    config = MagicMock()
    config.narrative_session.nms_image_url = "http://example.com/"

    metadata = {
        "type": "app",
        "appCell": {"app": {"spec": {"info": {"icon": {"url": "app_icon.png"}}}}},
    }

    result = get_icon(config, metadata)
    expected = {"type": "image", "icon": "http://example.com/app_icon.png"}
    assert result == expected


@pytest.mark.usefixtures("_sample_icon_data_file")
def test_get_icon_default_app_type() -> None:
    """Get the default app icon."""
    config = MagicMock()
    metadata = {
        "type": "app",
        "appCell": {"app": {"spec": {"info": {}}}},
    }

    result = get_icon(config, metadata)
    expected = {"type": "class", "icon": "fa-cube", "shape": "square", "color": "#673ab7"}
    assert result == expected


@pytest.mark.usefixtures("_sample_icon_data_file")
def test_get_icon_default_type() -> None:
    """Get the default of all default icon types."""
    config = MagicMock()
    metadata = {}

    result = get_icon(config, metadata)
    expected = {
        "type": "class",
        "icon": "fa-question-circle-o",
        "shape": "square",
        "color": "silver",
    }
    assert result == expected
