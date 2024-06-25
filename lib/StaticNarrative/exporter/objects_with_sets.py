"""Get workspace objects, including set information."""

import json
import os
from typing import Any

from installed_clients.WorkspaceClient import Workspace

from StaticNarrative.exporter.dynamic_service_client import DynamicServiceClient
from StaticNarrative.exporter.generic_set_navigator import GenericSetNavigator
from StaticNarrative.exporter.workspace_list_objects_iterator import (
    WorkspaceListObjectsIterator,
)


class ObjectsWithSets:
    def __init__(
        self: "ObjectsWithSets",
        set_api_client: DynamicServiceClient | None,
        workspace_client: Workspace,
        token: str | None = None,
        debug: bool = False,
    ) -> None:
        if set_api_client:
            self.set_api_client = set_api_client
        self.ws_client = workspace_client
        self.token = token
        self.generic_set_navigator = GenericSetNavigator(workspace_client, token)
        self.debug = debug

    def list_objects_with_sets(
        self: "ObjectsWithSets",
        ws_id: int | None = None,
        types: list[str] | None = None,
        include_metadata: int = 0,
        outdir: str = "",
        **kwargs,
    ) -> list[dict[str, Any]]:
        if not ws_id:
            msg = "ws_id is required"
            raise ValueError(msg)
        return self._list_objects_with_sets([ws_id], types, include_metadata, outdir)

    def _check_info_type(
        self: "ObjectsWithSets", info: list[str | Any], type_map: dict[str, Any] | None
    ) -> bool:
        if type_map is None:
            return True
        obj_type = info[2].split("-")[0]
        return type_map.get(obj_type, False)

    def _list_objects_with_sets(
        self: "ObjectsWithSets",
        workspaces: list[int | str],
        types: list[str] | None,
        include_metadata: int,
        outdir: str,
    ) -> list[dict[str, Any]]:
        """List objects with sets.

        :param self: this instance
        :type self: ObjectsWithSets
        :param workspaces: list of workspaces to fetch objects from
        :type workspaces: list[int|str]
        :param types: list of types to restrict the output to
        :type types: list[str]
        :param include_metadata: whether or not to retrieve object metadata
        :type include_metadata: int
        :param outdir: where to save output to if debugging
        :type outdir: str
        :return: _description_
        :rtype: dict[str, Any]
        """
        type_map = None
        if types is not None:
            type_map = {key: True for key in types}

        processed_refs = {}
        data = []

        if self.set_api_client:
            set_ret = self.set_api_client.call_method(
                "list_sets",
                [
                    {
                        "workspaces": workspaces,
                        "include_set_item_info": 1,
                        "include_metadata": include_metadata,
                        # TODO: implement infostruct returns!
                        # "infostruct": 1,
                    }
                ],
            )
        else:
            set_ret = self.generic_set_navigator.list_sets(
                {
                    "workspaces": workspaces,
                    "include_set_item_info": 1,
                    "include_metadata": include_metadata,
                }
            )

        if self.debug:
            with open(os.path.join(outdir, "list_sets.json"), "w") as fout:
                json.dump(set_ret, fout, indent=2, sort_keys=True)

        # return unless there are some sets in the workspace
        if not set_ret or "sets" not in set_ret:
            return data

        sets = set_ret["sets"]
        for set_info in sets:
            # Process
            target_set_items = [set_item["info"] for set_item in set_info["items"]]
            if self._check_info_type(set_info["info"], type_map):
                data_item = {
                    "object_info": set_info["info"],
                    "set_items": {"set_items_info": target_set_items},
                }
                data.append(data_item)
                processed_refs[set_info["ref"]] = data_item

        ws_info_list = []
        if len(workspaces) == 1:
            ws = workspaces[0]
            ws_id = None
            ws_name = None
            if str(ws).isdigit():
                ws_id = int(ws)
            else:
                ws_name = str(ws)
            ws_info_list.append(
                self.ws_client.get_workspace_info({"id": ws_id, "workspace": ws_name})
            )
        else:
            ws_map = {key: True for key in workspaces}
            ws_info_list = [
                ws_info
                for ws_info in self.ws_client.list_workspace_info({"perm": "r"})
                if ws_info[1] in ws_map or str(ws_info[0]) in ws_map
            ]

        for info in WorkspaceListObjectsIterator(
            self.ws_client,
            ws_info_list=ws_info_list,
            list_objects_params={"includeMetadata": include_metadata},
        ):
            item_ref = f"{info[6]}/{info[0]}/{info[4]}"
            if item_ref not in processed_refs and self._check_info_type(info, type_map):
                data_item = {"object_info": info}
                data.append(data_item)
                processed_refs[item_ref] = data_item

        return data
