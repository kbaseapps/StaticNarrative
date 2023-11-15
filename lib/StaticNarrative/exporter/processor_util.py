"""
Some catch-all functions for helping process Narrative cells.
"""
import html
import json
import os
from typing import T
from urllib.parse import quote

from installed_clients.authclient import KBaseAuth
from installed_clients.WorkspaceClient import Workspace

from StaticNarrative import STATIC_NARRATIVE_BASE_DIR

ICON_DATA = None


def _load_icon_data() -> None:
    # this should access the local folder
    icon_json = os.path.join(STATIC_NARRATIVE_BASE_DIR, "data", "icons.json")
    with open(icon_json) as icon_file:
        global ICON_DATA
        ICON_DATA = json.load(icon_file)


def build_report_view_data(
    host: str, ws_client: Workspace, result: dict[str, T] | list[dict[str, T]]
) -> dict[str, str | list | dict]:
    """
    Returns a structure like this:
    {
        html: {
            height: max height string for iframes (default = 500px, unless present in report),
            set_height: boolean - if True, then apply height to the height style value as well.
            direct: string (optional) - direct html to plop in the page,
            iframe_style: string (optional) - styling for direct html iframe,
            links: [{
                url: string,
                name: string,
                description: string,
                handle: ?
                label: ?
            }],
            paths: [ path1, path2, path3, ... ] for all urls in links (just a convenience),
            link_idx: index of paths to use
                (this is a little funky, might get cleared up in a later iteration.)
                (I suspect this'll be here 3 years later. Today's 2/13/2020. Let's see!)
            file_links: [{
                'URL': 'https://ci.kbase.us/services/shock-api/node/a2625b71-48d5-4ba6-8603-355485508da8',
                'description': 'JGI Metagenome Assembly Report',
                'handle': 'KBH_253154',
                'label': 'assembly_report',
                'name': 'assembly_report.zip'
            }]
        }
        objects: [{
            'upa': '...',
            'name': 'foo',
            'type': '...',
            'description': '...'
        }]
        summary: '',
        summary_height: height string for summary panel (default = 500px unless specified in report),
        report: ''
    }
    """
    if not result:
        return {}
    if not isinstance(result, list):
        result = [result]
    if (
        not result[0]
        or not isinstance(result[0], dict)
        or not result[0].get("report_name")
        or not result[0].get("report_ref")
    ):
        return {}
    report_ref = result[0]["report_ref"]
    report = ws_client.get_objects2({"objects": [{"ref": report_ref}]})["data"][0][
        "data"
    ]
    """{'direct_html': None,
     'direct_html_link_index': None,
     'file_links': [],
     'html_links': [],
     'html_window_height': None,
     'objects_created': [{'description': 'Annotated genome', 'ref': '43666/6/1'}],
     'summary_window_height': None,
     'text_message': 'Genome saved to: wjriehl:narrative_1564507007662/some_genome\nNumber of genes predicted: 3895\nNumber of protein coding genes: 3895\nNumber of genes with non-hypothetical function: 2411\nNumber of genes with EC-number: 1413\nNumber of genes with Seed Subsystem Ontology: 1081\nAverage protein length: 864 aa.\n',
     'warnings': []}
    """
    created_objs = []
    if report.get("objects_created"):
        report_objs_created = report["objects_created"]
        # make list to look up obj types with get_object_info3
        info_lookup = [{"ref": o["ref"]} for o in report_objs_created]
        infos = ws_client.get_object_info3({"objects": info_lookup, "ignoreErrors": 1})[
            "infos"
        ]

        for idx, info in enumerate(infos):
            if info:
                created_objs.append(
                    {
                        "upa": report_objs_created[idx]["ref"],
                        "description": report_objs_created[idx].get("description", ""),
                        "name": info[1],
                        "type": info[2].split("-")[0].split(".")[-1],
                        "link": host + "/#dataview/" + report_objs_created[idx]["ref"],
                    }
                )
    html_height = report.get("html_window_height")
    if html_height is None:
        html_height = 500
    html = {"height": f"{html_height}px", "set_height": True}
    if report.get("direct_html"):
        if not report.get("direct_html").startswith("<html"):
            html["set_height"] = False
        html["direct"] = "data:text/html;charset=utf-8," + quote(
            report.get("direct_html")
        )

    if report.get("html_links"):
        idx = report.get("direct_html_link_index", 0)
        if idx is None or idx < 0 or idx >= len(report["html_links"]):
            idx = 0
        html["links"] = report["html_links"]
        html["paths"] = []
        for i, link in enumerate(html["links"]):
            html["paths"].append(f'/api/v1/{report_ref}/$/{i}/{link["name"]}')
        html["link_idx"] = idx

    if report.get("file_links"):
        html["file_links"] = report["file_links"]

    summary_height = report.get("summary_window_height")
    if summary_height is None:
        summary_height = 500

    html["iframe_style"] = f"max-height: {html['height']}"
    if html["set_height"]:
        html["iframe_style"] += f"; height: {html['height']}"
    else:
        html["iframe_style"] += "; height: auto"
    return {
        "objects": created_objs,
        "summary": report.get("text_message", ""),
        "summary_height": f"{summary_height}px",
        "html": html,
    }


def get_icon(config: dict[str, T], metadata: dict[str, T]) -> dict[str, str]:
    """
    Should return a dict with keys "type" and "icon"
    * if "type" = image, then "icon" second should be the src.
    * if "type" = class, "icon" should be the full class to use to render the icon -
        "fa fa-right-arrow", for instance.
    * also, if "type" == "class", then the keys "color" and "shape" should also be present.
    """
    icon = {"type": "image", "icon": None}
    if metadata.get("type") == "data":
        icon["type"] = "class"
        icon.update(
            get_data_icon(
                metadata.get("dataCell", {}).get("objectInfo", {}).get("typeName")
            )
        )
    elif metadata.get("type") == "output":
        icon["type"] = "class"
        icon["icon"] = "fa-arrow-right"
        icon["color"] = "silver"
        icon["shape"] = "square"
    elif metadata.get("type") == "app":
        if "icon" in metadata.get("appCell", {}).get("app", {}).get("spec", {}).get(
            "info", {}
        ):
            icon["type"] = "image"
            icon["icon"] = (
                config.narrative_session.nms_image_url
                + metadata["appCell"]["app"]["spec"]["info"]["icon"]["url"]
            )
        else:
            icon["type"] = "class"
            icon["icon"] = "fa-cube"
            icon["shape"] = "square"
            icon["color"] = "#673ab7"
    else:
        icon["type"] = "class"
        icon["icon"] = "fa-question-circle-o"
        icon["shape"] = "square"
        icon["color"] = "silver"
    return icon


def get_data_icon(obj_type: str) -> dict[str, str]:
    if ICON_DATA is None:
        _load_icon_data()

    icon_info = {
        "icon": ICON_DATA["data"]["DEFAULT"],
        "color": ICON_DATA["colors"][0],
        "shape": "circle",
    }
    if obj_type in ICON_DATA["data"]:
        icon_info["icon"] = " ".join(ICON_DATA["data"][obj_type])
    if obj_type in ICON_DATA["color_mapping"]:
        icon_info["color"] = ICON_DATA["color_mapping"][obj_type]
    return icon_info


def get_authors(config: dict[str, T], wsid: str) -> list[dict[str, str]]:
    ws_client = Workspace(
        url=config.narrative_session.ws_url, token=config.narrative_session.token
    )
    ws_info = ws_client.get_workspace_info({"id": wsid})
    author_id_list = [ws_info[2]]

    other_authors = ws_client.get_permissions({"id": wsid})

    for author in sorted(other_authors.keys()):
        if (
            author != "*"
            and other_authors[author] in ["w", "a"]
            and author not in author_id_list
        ):
            author_id_list.append(author)

    auth = KBaseAuth(config.narrative_session.auth_url)
    disp_names = {}
    try:
        disp_names = auth.get_display_names(
            config.narrative_session.token, author_id_list
        )
    except Exception as e:
        print(str(e))

    return [
        {
            "id": author,
            "name": html.escape(disp_names.get(author, author)),
            "path": config.narrative_session.profile_page_url + author,
        }
        for author in author_id_list
    ]
