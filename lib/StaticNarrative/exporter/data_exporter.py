"""Fetches data to be exported as part of the Static Narrative creation."""

import json
from pathlib import Path
from typing import Any

from installed_clients.WorkspaceClient import Workspace

from StaticNarrative.constants import NARRATIVE_TYPE, OBJ_INFO, OUTPUT_DATA_FILE
from StaticNarrative.exporter.dynamic_service_client import DynamicServiceClient
from StaticNarrative.exporter.icon_util import get_data_icon
from StaticNarrative.exporter.objects_with_sets import ObjectsWithSets
from StaticNarrative.upa import generate_upa

IGNORED_TYPES = [NARRATIVE_TYPE]
SET_ITEMS = "set_items"
SET_ITEMS_INFO = "set_items_info"


def export_narrative_data(
    ws_client: Workspace,
    wsid: int,
    token: str,
    output_dir: str | Path,
    set_api_client: DynamicServiceClient | None = None,
    debug: bool = False,
) -> dict[str, Any]:
    """Exports data from a Narrative into an attached JSON file.

    Returns the output path to the JSON file as well as the data that was dumped into it.
    This includes a list of types and the data itself.

    The returned dictionary has the following format:
    {
        output_path: str,
        types: {
            type name (str): {
                count: int,
                icon: {
                    icon: str,
                    color: str (hex number),
                    shape (str, probably circle)
                }
            }
        },
        data: [
            reference (str),
            name (str),
            type (str),
            save date (str, timestamp),
            metadata: (dict[str, str])
        ]
    }

    types and data (above) are dumped to data.json
    """
    # Call ObjectsWithSets to retrieve data, including any sets in the workspace
    ows = ObjectsWithSets(workspace_client=ws_client, set_api_client=set_api_client, token=token)
    ws_data = ows.list_objects_with_sets(ws_id=wsid, include_metadata=1)

    indexed_data = {}
    type_info = {}
    for item in ws_data:
        # add the item to the index of ws objects and types
        _index_obj(item, type_info, indexed_data)

        # if this is a set, go through each item in the set and add it to indexed_data
        if SET_ITEMS in item and SET_ITEMS_INFO in item[SET_ITEMS]:
            item[SET_ITEMS]["upas"] = []
            for set_item in item[SET_ITEMS][SET_ITEMS_INFO]:
                set_item_upa = generate_upa(set_item)
                item[SET_ITEMS]["upas"].append(set_item_upa)
                _index_obj({OBJ_INFO: set_item}, type_info, indexed_data)

    # generate a list of data for output, sorted by object name
    reshaped_data = [_reshape_obj(upa, val) for upa, val in indexed_data.items()]

    # Sort and dump to file.
    output_data = {
        "data": sorted(reshaped_data, key=lambda x: x[1].lower()),
        "types": type_info,
    }

    output_path = Path(output_dir) / OUTPUT_DATA_FILE
    with output_path.open("w") as outfile:
        json.dump(output_data, outfile)
    output_data["path"] = str(output_path)
    output_data["indexed_data"] = indexed_data
    return output_data


def _index_obj(
    item: dict[str, Any], type_info: dict[str, Any], indexed_data: dict[str, Any]
) -> None:
    """Index by object ID and save the type information."""
    obj = item[OBJ_INFO]
    obj_type = obj[2].split("-")[0]
    if obj_type in IGNORED_TYPES:
        return
    obj_upa = generate_upa(item[OBJ_INFO])
    type_name = obj_type.split(".")[-1]
    if type_name not in type_info:
        type_info[type_name] = {"count": 0, "icon": get_data_icon(type_name)}
    type_info[type_name]["count"] += 1
    indexed_data[obj_upa] = item


def _reshape_obj(obj_upa: str, obj: dict[str, Any]) -> list[str | dict[str, Any]]:
    """Strip out useful object info, return as a list.

    Just pulls out the relevant info from object info, and mashes it into
    something more useful for the Static Narrative data browser.
    Takes a KBase object from the Workspace and returns the following list:
    [
        UPA,
        name,
        type,
        timestamp,
        metadata (or empty dict)
    ]
    """
    if OBJ_INFO not in obj:
        msg = "Invalid KBase obj data format: " + json.dumps(obj)
        raise ValueError(msg)

    return [
        obj_upa,
        obj[OBJ_INFO][1],
        obj[OBJ_INFO][2],
        obj[OBJ_INFO][3],
        obj[OBJ_INFO][10],
    ]
