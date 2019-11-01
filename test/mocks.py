import requests
import requests_mock
from typing import Dict, List
import json


def _mock_adapter(ws_id: int = None,
                  ref_to_file: Dict[str, str] = {},
                  ref_to_info: Dict[str, List] = {},
                  ws_info: List = [],
                  user_map: Dict[str, str] = {},
                  static_nar_ver: int = None):
    """
    Sets up mock calls as a requests_mock adapter function.
    Mocks POST calls to:
        Workspace.get_objects2,
        Workspace.get_workspace_info,
        Workspace.get_object_info3
    Mocks GET calls to:
        Auth (api/V2/users)
    """
    def mock_adapter(request):
        response = requests.Response()
        response.status_code = 200
        rq_method = request.method.upper()
        if rq_method == "POST":
            params = request.json().get("params")
            print(params)
            method = request.json().get("method")

            result = []
            if method == "Workspace.get_objects2":
                # maps a workspace object reference to returns from a file,
                # fails if no matching file present.
                # only gets called with a single obj requested, so craft the
                # response that way
                ref = params[0].get("objects", [{}])[0].get("ref")
                print(ref_to_file)
                print(isinstance(ref_to_file, dict))
                if ref not in ref_to_file:
                    response.status_code = 500
                    result = [{"error": f"no object with reference {ref}"}]
                else:
                    result = [{"data": [_get_object_from_file(ref_to_file[ref])]}]
            elif method == "Workspace.get_object_info3":
                # list of created objects for reports - can fail.
                    info_list = list()
                    paths = list()
                    for obj in params[0].get("objects"):
                        ref = obj["ref"]
                        info_list.append(ref_to_info.get(ref, _fake_obj_info(ref)))
                        paths.append([ref])
                    result = [{
                        "infos": info_list,
                        "paths": paths
                    }]
            elif method == "Workspace.list_objects":
                # list of objects in a workspace. can fail with perms error
                # 10/31/2019 - don't need yet.
                pass
            elif method == "Workspace.get_workspace_info":
                # return workspace info object, with or w/o extra metadata field
                # for static narrative
                if static_nar_ver:
                    ws_info[8]["static_nar_ver"] = static_nar_ver
                result = [ws_info]
            response._content = bytes(json.dumps({
                "result": result,
                "version": "1.1"
            }), "UTF-8")
        elif rq_method == "GET":
            print(request.url)
            if "/api/V2/users/?list=" in request.url:
                response._content = bytes(json.dumps(user_map), "UTF-8")
        return response

    return mock_adapter


def _fake_obj_info(ref: str):
    split_ref = ref.split('/')
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
        None
    ]


def _get_object_from_file(filename: str):
    """
    This should be a JSON file representing a workspace data object.
    If it's not JSON, it'll crash.
    """
    print("Trying to open " + filename)
    with open(filename, "r") as f:
        obj = json.load(f)
    return obj


def set_up_ok_mocks(rqm,
                    ws_id: int,
                    ref_to_file: Dict,
                    ref_to_info: Dict,
                    ws_info: List,
                    user_map: Dict):
    print(ref_to_file)
    print(isinstance(ref_to_file, dict))
    rqm.add_matcher(_mock_adapter(ws_id=ws_id,
                                  ref_to_file=ref_to_file,
                                  ref_to_info=ref_to_info,
                                  ws_info=ws_info,
                                  user_map=user_map))


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

