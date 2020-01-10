from typing import List
from installed_clients.NarrativeServiceClient import NarrativeService
from .processor_util import get_data_icon
import os
import json

IGNORED_TYPES = ["KBaseNarrative.Narrative"]


def export_narrative_data(wsid: int, output_dir: str, service_wizard_url: str, token: str) -> str:
    # just call out to NarrativeService.list_objects_with_sets.
    ns_client = NarrativeService(url=service_wizard_url, token=token)
    ws_data = ns_client.list_objects_with_sets({
        "ws_id": wsid,
        "includeMetadata": 1
    })['data']
    filtered_data = []
    type_info = {}
    for item in ws_data:
        obj = item["object_info"]
        obj_type = obj[2].split("-")[0]
        if obj_type in IGNORED_TYPES:
            continue
        type_name = obj_type.split('.')[-1]
        if type_name not in type_info:
            type_info[type_name] = {
                'count': 0,
                'icon': get_data_icon(type_name)
            }
        filtered_data.append(_reshape_obj(obj))
        type_info[type_name]['count'] += 1

    # Maybe sort it later. For now, dump to file.
    output_data = {
        'data': filtered_data,
        'types': type_info
    }

    output_path = os.path.join(output_dir, "data.json")
    with open(output_path, "w") as outfile:
        json.dump(output_data, outfile)
    return output_path


def _reshape_obj(obj_info: List) -> List:
    """
    Just pulls out the relevant info from object info, and mashes it into
    something more useful for the Static Narrative data browser.
    Takes an Object Info tuple from the Workspace and returns the following list:
    [
        UPA,
        name,
        type,
        timestamp,
        metadata (or empty Dict)
    ]
    """
    return [
        f"{obj_info[6]}/{obj_info[0]}/{obj_info[4]}",
        obj_info[1],
        obj_info[2],
        obj_info[3],
        obj_info[10]
    ]
