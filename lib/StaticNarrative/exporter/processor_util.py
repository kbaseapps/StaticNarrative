"""Some catch-all functions for helping process Narrative cells."""

import html
import json
import os
from typing import Any
from urllib.parse import quote

import requests
from installed_clients.WorkspaceClient import Workspace
from traitlets.config import Config

from StaticNarrative import STATIC_NARRATIVE_BASE_DIR
from StaticNarrative.upa import generate_upa


def build_report_view_data(
    ws_client: Workspace,
    indexed_data: dict[str, Any],
    host: str,
    result: dict[str, Any] | list[dict[str, Any]],
) -> dict[str, str | list | dict]:
    """Build the data structure used to represent a report in a static narrative.

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
    if isinstance(result, list):
        result = result[0]  # what about the rest of the list?!
    if (
        not result
        or not isinstance(result, dict)
        or not result.get("report_name")
        or not result.get("report_ref")
    ):
        return {}
    report_ref = result["report_ref"]

    if report_ref in indexed_data:
        report = indexed_data[report_ref]["data"]
    else:
        try:
            report = ws_client.get_objects2({"objects": [{"ref": report_ref}]})["data"][0]["data"]
        except Exception:
            # can't retrieve report - e.g. if it has been deleted
            return {}

    """
    {
        'direct_html': None,
        'direct_html_link_index': None,
        'file_links': [],
        'html_links': [],
        'html_window_height': None,
        'objects_created': [{'description': 'Annotated genome', 'ref': '43666/6/1'}],
        'summary_window_height': None,
        'text_message': 'Genome saved to: wjriehl:narrative_1564507007662/some_genome\nNumber of genes predicted: 3895\nNumber of protein coding genes: 3895\nNumber of genes with non-hypothetical function: 2411\nNumber of genes with EC-number: 1413\nNumber of genes with Seed Subsystem Ontology: 1081\nAverage protein length: 864 aa.\n',
        'warnings': []
    }
    """
    created_objs = get_created_objects_from_report(ws_client, indexed_data, host, report)

    html_height = report.get("html_window_height")
    if html_height is None:
        html_height = 500
    html = {"height": f"{html_height}px", "set_height": True}
    if report.get("direct_html"):
        if not report.get("direct_html").startswith("<html"):
            html["set_height"] = False
        html["direct"] = "data:text/html;charset=utf-8," + quote(report.get("direct_html"))

    if report.get("html_links"):
        idx = report.get("direct_html_link_index", 0)
        if idx is None or idx < 0 or idx >= len(report["html_links"]):
            idx = 0
        html["links"] = report["html_links"]
        html["paths"] = [
            f'/api/v1/{report_ref}/$/{i}/{link["name"]}' for i, link in enumerate(html["links"])
        ]
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


def get_created_objects_from_report(
    ws_client: Workspace,
    indexed_data: dict[str, Any],
    host: str,
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create a data structure to represent objects created by an app.

    :param ws_client: workspace client
    :type ws_client: Workspace
    :param indexed_data: KBase objects, indexed by UPA
    :type indexed_data: dict[str, Any]
    :param host: string representing the KBase host for URL generation
    :type host: str
    :param report: report data structure
    :type report: dict[str, Any]
    :return: list of data structures for representing objects
    :rtype: list[dict[str, Any]]
    """
    if not report.get("objects_created"):
        return []

    report_objs_created = report["objects_created"]
    # make list to look up obj types with get_object_info3
    info_lookup = [{"ref": o["ref"]} for o in report_objs_created if o["ref"] not in indexed_data]
    if info_lookup:
        result = ws_client.get_object_info3({"objects": info_lookup, "ignoreErrors": 1})
        if result and "infos" in result:
            for ix, obj in enumerate(result["infos"]):
                if obj:
                    upa = generate_upa(obj)
                    indexed_data[upa] = {"object_info": obj}
                else:
                    indexed_data[info_lookup[ix]["ref"]] = None

    return [
        {
            "upa": o["ref"],
            "description": o.get("description", ""),
            "name": indexed_data[o["ref"]]["object_info"][1] or "unknown",
            "type": indexed_data[o["ref"]]["object_info"][2].split("-")[0].split(".")[-1]
            or "unknown",
            "link": host + "/#dataview/" + o["ref"],
        }
        for o in report_objs_created
        if indexed_data[o["ref"]]
    ]


def get_display_names(auth_url: str, token: str, user_ids: list[str]) -> dict[str, Any]:
    """Given a list of user IDs, get the corresponding display names."""
    headers = {"Authorization": token}
    r = requests.get(
        f"{auth_url}/api/V2/users/?list=" + ",".join(user_ids),
        headers=headers,
        timeout=30 * 60,  # same as baseclient default
    )
    r.raise_for_status()
    return r.json()


def get_authors(ws_client: Workspace, config: Config, wsid: str | int) -> list[dict[str, str]]:
    """Retrieve the list of people with workspace admin and write permissions."""
    ws_info = ws_client.get_workspace_info({"id": wsid})
    ws_author = ws_info[2]

    other_authors = ws_client.get_permissions({"id": wsid}) or []

    author_id_set = {
        author
        for author in other_authors
        if other_authors[author] in ["w", "a"] and author != "*" and author != ws_author
    }

    author_id_list = [ws_author, *sorted(author_id_set)]
    disp_names = {}
    try:
        disp_names = get_display_names(config.auth_url, config.token, author_id_list)
    except Exception as e:
        print(str(e))

    return [
        {
            "id": author,
            "name": html.escape(disp_names.get(author, author)),
            "path": config.profile_page_path + author,
        }
        for author in author_id_list
    ]
