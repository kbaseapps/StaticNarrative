import json
import os
from copy import deepcopy
from test import TEST_BASE_DIR
from typing import Any

import requests


def _mock_adapter(
    ref_to_file: dict[str, str] | None = None,
    ref_to_info: dict[str, list] | None = None,
    ws_info: list | None = None,
    user_map: dict[str, str] | None = None,
    ws_perms: dict[int, dict[str, str]] | None = None,
    ws_obj_info_file: str | None = None,
):
    """
    Sets up mock calls as a requests_mock adapter function.
    Mocks POST calls to:
        Workspace.get_objects2,
        Workspace.get_workspace_info,
        Workspace.get_object_info3
    Mocks GET calls to:
        Auth (api/V2/users)
    :param ref_to_file: dict - maps from a workspace ref to the path to a file containing the
        object JSON. used in Workspace.get_objects2
    :param ref_to_info: dict - maps from a workspace ref to a object info list for that object.
        Used in Workspace.get_object_info3
    :param ws_info: list - the Workspace info that should be returned on a call to
        Workspace.get_workspace_info
    :param ws_perms: dict - a mapping from a workspace id to a dict with user permissions on that ws
    :param user_map: dict - a mapping from user id to full name, used in calls to Auth
        GET api/V2/users
    """

    for prop in [ref_to_file, ref_to_info, user_map, ws_perms]:
        if prop is None:
            prop = {}
    if ws_info is None:
        ws_info = []
    workspace_meta = {}

    def mock_adapter(request):
        response = requests.Response()
        response.status_code = 200
        rq_method = request.method.upper()
        if rq_method == "POST":
            params = request.json().get("params")
            method = request.json().get("method")
            result = []
            if method == "Workspace.get_objects2":
                # maps a workspace object reference to returns from a file,
                # fails if no matching file present.
                # only gets called with a single obj requested, so craft the
                # response that way
                ref = params[0].get("objects", [{}])[0].get("ref")
                if ref not in ref_to_file:
                    response.status_code = 500
                    result = [{"error": f"no object with reference {ref}"}]
                else:
                    result = [{"data": [_get_object_from_file(ref_to_file[ref])]}]
            elif method == "Workspace.get_object_info3":
                # list of created objects for reports - can fail.
                info_list = []
                paths = []
                for obj in params[0].get("objects"):
                    ref = obj["ref"]
                    info_list.append(ref_to_info.get(ref, _fake_obj_info(ref)))
                    paths.append([ref])
                result = [{"infos": info_list, "paths": paths}]
            elif method == "Workspace.list_objects":
                # list of objects in a workspace. can fail with perms error
                # 10/31/2019 - don't need yet.
                pass
            elif method == "Workspace.get_workspace_info":
                # return workspace info object, with or w/o extra metadata field
                # for static narrative
                ws_id = params[0].get("id")
                info = deepcopy(ws_info)
                if ws_id in workspace_meta:
                    info[8].update(workspace_meta[ws_id])
                result = [info]
            elif method == "Workspace.alter_workspace_metadata":
                # returns nothing, so this is simple.
                # but every proceeding get_workspace_info call should return
                # updated metadata.
                ws_id = params[0].get("wsi", {}).get("id")
                workspace_meta[ws_id] = params[0].get("new")
            elif method == "Workspace.get_permissions":
                ws_id = params[0].get("id")
                result = [ws_perms.get(ws_id, {})]
            elif method == "ServiceWizard.get_service_status":
                result = [
                    {"url": "https://something.kbase.us/service/narrative_service_url"}
                ]
            elif method == "NarrativeService.list_objects_with_sets":
                if ws_obj_info_file is not None:
                    result = [_get_object_from_file(ws_obj_info_file)]
                else:
                    result = [{"data": []}]
            elif method == "NarrativeMethodStore.get_method_full_info":
                tag = params[0]["tag"]
                ids = params[0]["ids"]
                result = [_get_fake_nms_info(tag, ids)]
            response._content = bytes(
                json.dumps({"result": result, "version": "1.1"}), "UTF-8"
            )
        elif rq_method == "GET" and "/api/V2/users/?list=" in request.url:
            response._content = bytes(json.dumps(user_map), "UTF-8")
        return response

    return mock_adapter


def _get_fake_nms_info(tag: str, ids: list) -> list:
    app_infos = _get_object_from_file("data/nms_info.json")[tag]
    ret = []
    for i in ids:
        if i in app_infos:
            ret.append(app_infos[i])
        else:
            ret.append(
                {
                    "id": "SomeModule/some_app",
                    "name": "Some Unknown App",
                    "publications": [],
                }
            )
    return ret


def _fake_obj_info(ref: str) -> list[None | str | int]:
    split_ref = ref.split("/")
    return [
        split_ref[1],
        "Fake_object_name",
        "FakeModule.FakeObject-1.0",
        "2019-10-24T21:51:17+0000",
        split_ref[2],
        "some_user",
        split_ref[0],
        "fake_workspace",
        "some_md5",
        12345,
        None,
    ]


def _get_object_from_file(filename: str) -> dict[str, Any]:
    """
    This should be a JSON file representing workspace data or some other JSON data
    returned from a service.
    If it's not JSON, it'll crash.
    """
    with open(os.path.join(TEST_BASE_DIR, filename)) as f:
        return json.load(f)


def set_up_ok_mocks(
    rqm,
    ref_to_file: dict | None = None,
    ref_to_info: dict | None = None,
    ws_info: list | None = None,
    ws_perms: dict | None = None,
    user_map: dict | None = None,
    ws_obj_info_file: str | None = None,
):
    rqm.add_matcher(
        _mock_adapter(
            ref_to_file=ref_to_file,
            ref_to_info=ref_to_info,
            ws_info=ws_info,
            ws_perms=ws_perms,
            user_map=user_map,
            ws_obj_info_file=ws_obj_info_file,
        )
    )


def mock_auth_ok(user_id, token):
    pass


def mock_auth_bad_token(token):
    pass


def mock_ws_narrative_fetch(narrative_ref):
    pass


def mock_ws_narrative_fetch_forbidden(narrative_ref):
    pass


def mock_ws_info(ws_id):
    pass


def mock_ws_info_unauth(ws_id):
    pass


def mock_ws_bad(rqm, msg):
    """
    Always returns a 500 from a workspace call, triggering a ServerError
    """

    def mock_adapter_bad_ws(request):
        response = requests.Response()
        response.status_code = 500
        response._content = bytes(
            json.dumps(
                {
                    "error": {
                        "code": -32500,
                        "message": msg,
                        "error": "long Java vomit stacktrace",
                        "name": "JSONRPCError",
                    },
                    "version": "1.1",
                    "id": request.json().get("id", "12345"),
                }
            ),
            "UTF-8",
        )
        return response

    rqm.add_matcher(mock_adapter_bad_ws)
