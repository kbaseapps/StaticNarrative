import json
import os
from typing import T

from installed_clients.NarrativeServiceClient import NarrativeService

from .processor_util import get_data_icon

IGNORED_TYPES = ["KBaseNarrative.Narrative"]


def export_narrative_data(
    wsid: int, output_dir: str, service_wizard_url: str, token: str
) -> dict[str, T]:
    """
    Exports data from a Narrative into an attached JSON file.
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
    # just call out to NarrativeService.list_objects_with_sets.
    ns_client = NarrativeService(url=service_wizard_url, token=token)
    ws_data = ns_client.list_objects_with_sets({"ws_id": wsid, "includeMetadata": 1})[
        "data"
    ]
    filtered_data = []
    type_info = {}
    for item in ws_data:
        obj = item["object_info"]
        obj_type = obj[2].split("-")[0]
        if obj_type in IGNORED_TYPES:
            continue
        type_name = obj_type.split(".")[-1]
        if type_name not in type_info:
            type_info[type_name] = {"count": 0, "icon": get_data_icon(type_name)}
        filtered_data.append(_reshape_obj(obj))
        type_info[type_name]["count"] += 1

    # Maybe sort it later. For now, dump to file.
    output_data = {
        "data": sorted(filtered_data, key=lambda o: o[1].lower()),
        "types": type_info,
    }

    output_path = os.path.join(output_dir, "data.json")
    with open(output_path, "w") as outfile:
        json.dump(output_data, outfile)
    output_data["path"] = output_path
    return output_data


def _reshape_obj(obj_info: list[str, str | dict[str, T]]) -> list[str | dict[str, T]]:
    """
    Just pulls out the relevant info from object info, and mashes it into
    something more useful for the Static Narrative data browser.
    Takes an Object Info tuple from the Workspace and returns the following list:
    [
        UPA,
        name,
        type,
        timestamp,
        metadata (or empty dict)
    ]
    """
    return [
        f"{obj_info[6]}/{obj_info[0]}/{obj_info[4]}",
        obj_info[1],
        obj_info[2],
        obj_info[3],
        obj_info[10],
    ]
