"""Tests for the data exporter."""

from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.constants import OBJ_INFO, OUTPUT_DATA_FILE
from StaticNarrative.exporter.data_exporter import (
    SET_ITEMS,
    SET_ITEMS_INFO,
    _reshape_obj,
    export_narrative_data,
)

# Constants used in the function
IGNORED_TYPES = ["Module.Type", "Module.IgnoredType"]


@pytest.fixture()
def narrative_data() -> list[dict[str, Any]]:
    """Sample narrative data."""
    return [
        {
            OBJ_INFO: [
                1,
                "name",
                "Module.Type-1.0",
                "timestamp",
                2,
                None,
                123,
                None,
                None,
                None,
                {},
            ],
            SET_ITEMS: {SET_ITEMS_INFO: []},
        },
        {
            OBJ_INFO: [
                2,
                "another_name",
                "Module.AnotherType-1.0",
                "timestamp",
                1,
                None,
                123,
                None,
                None,
                None,
                {},
            ],
        },
    ]


def test_export_narrative_data(
    fake_token: str,
    tmp_path: Path,
    narrative_data: list[dict[str, Any]],
    mocker: Callable[..., Generator[Any, None, None]],
) -> None:
    mocker.patch(
        "StaticNarrative.exporter.objects_with_sets.ObjectsWithSets.list_objects_with_sets",
        return_value=narrative_data,
    )

    result = export_narrative_data(MagicMock(), 123, fake_token, tmp_path)

    assert "data" in result
    assert "types" in result
    assert "path" in result
    assert result["path"] == str(tmp_path / OUTPUT_DATA_FILE)
    assert "AnotherType" in result["types"]
    assert "Type" in result["types"]
    assert result["types"]["AnotherType"]["count"] == 1
    assert result["types"]["Type"]["count"] == 1
    assert len(result["data"]) == 2
    assert result["data"][0] == [
        "123/2/1",
        "another_name",
        "Module.AnotherType-1.0",
        "timestamp",
        {},
    ]

    assert result["data"][1] == [
        "123/1/2",
        "name",
        "Module.Type-1.0",
        "timestamp",
        {},
    ]


def test_reshape_obj() -> None:
    """Check that an object is reshaped appropriately."""
    obj = {
        OBJ_INFO: [
            1,
            "name",
            "Module.Type-1.0",
            "timestamp",
            None,
            None,
            None,
            None,
            None,
            None,
            {},
        ]
    }
    reshaped = _reshape_obj("1/1/1", obj)
    assert reshaped == ["1/1/1", "name", "Module.Type-1.0", "timestamp", {}]


def test_reshape_obj_invalid_format() -> None:
    """Ensure an invalid object returns an error."""
    with pytest.raises(ValueError, match="Invalid KBase obj data format: "):
        _reshape_obj("1/1/1", {})


def test_export_narrative_data_ignored_types(
    fake_token: str,
    tmp_path: Path,
    mocker: Callable[..., Generator[Any, None, None]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the appropriate data is returned when the type is an ignored type."""
    narrative_data = [
        {
            OBJ_INFO: [
                4,
                "name",
                "Module.IgnoredType-1.0",
                "timestamp",
                5,
                None,
                123,
                None,
                None,
                None,
                {},
            ],
        }
    ]
    mocker.patch(
        "StaticNarrative.exporter.objects_with_sets.ObjectsWithSets.list_objects_with_sets",
        return_value=narrative_data,
    )
    mock_get_data_icon = mocker.patch("StaticNarrative.exporter.icon_util.get_data_icon")
    mock_generate_upa = mocker.patch("StaticNarrative.upa.generate_upa")
    mock_reshape_obj = mocker.patch("StaticNarrative.exporter.data_exporter._reshape_obj")

    monkeypatch.setattr("StaticNarrative.exporter.data_exporter.IGNORED_TYPES", IGNORED_TYPES)
    result = export_narrative_data(MagicMock(), 123, fake_token, tmp_path)

    assert "data" in result
    assert "types" in result
    assert len(result["data"]) == 0
    assert len(result["types"]) == 0
    mock_get_data_icon.assert_not_called()
    mock_generate_upa.assert_not_called()
    mock_reshape_obj.assert_not_called()


def test_export_narrative_data_sets(
    fake_token: str,
    tmp_path: Path,
    mocker: Callable[..., Generator[Any, None, None]],
) -> None:
    """Test that the appropriate data is returned when the output contains sets."""
    narrative_data = [
        {
            OBJ_INFO: [
                1,
                "name",
                "Module.SomeSortOfSet-1.0",
                "timestamp",
                1,
                None,
                123,
                None,
                None,
                None,
                {},
            ],
            SET_ITEMS: {
                SET_ITEMS_INFO: [
                    [
                        2,
                        "item_name",
                        "Module.ItemType-1.0",
                        "timestamp",
                        1,
                        None,
                        123,
                        None,
                        None,
                        None,
                        {},
                    ],
                    [
                        3,
                        "another_item_name",
                        "Module.ItemType-1.0",
                        "timestamp",
                        1,
                        None,
                        123,
                        None,
                        None,
                        None,
                        {},
                    ],
                ]
            },
        }
    ]
    mocker.patch(
        "StaticNarrative.exporter.objects_with_sets.ObjectsWithSets.list_objects_with_sets",
        return_value=narrative_data,
    )

    result = export_narrative_data(MagicMock(), 123, fake_token, tmp_path)

    assert "data" in result
    assert "types" in result
    assert "SomeSortOfSet" in result["types"]
    assert "ItemType" in result["types"]
    assert result["types"]["SomeSortOfSet"]["count"] == 1
    assert result["types"]["ItemType"]["count"] == 2
    assert len(result["data"]) == 3
    upa_list = [d[0] for d in result["data"]]
    assert upa_list == ["123/3/1", "123/2/1", "123/1/1"]
