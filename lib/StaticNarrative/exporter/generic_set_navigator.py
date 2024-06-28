"""Generic set queries."""

import json
import time
from typing import Any

from installed_clients.WorkspaceClient import Workspace

from StaticNarrative import util
from StaticNarrative.exporter.workspace_list_objects_iterator import WorkspaceListObjectsIterator

REF = "ref"


class GenericSetNavigator:
    """Generic set-related functionality."""

    SET_TYPES = ["KBaseSets.ReadsSet"]
    DEBUG = False

    def __init__(
        self: "GenericSetNavigator", workspace_client: Workspace, token: str | None = None
    ) -> None:
        """Create a new GenericSetNavigator instance."""
        self.ws = workspace_client
        self.token = token

    def list_sets(self: "GenericSetNavigator", params: dict[str, Any]) -> dict[str, Any]:
        """Get a list of the top-level sets.

        Top-level sets are those that are unreferenced by any other sets in the specified workspace.
        Set item references are always returned, ws info for each of those items can optionally be included too.

        params: dict with keys-
            workspace - string - workspace to search for sets
            workspaces - list<string> - list of workspaces to search for sets
            include_metadata - [0, 1], default=0 - if 1, get metadata for set items
            include_set_item_info [0, 1], default=0 - if 1, get Workspace object_info
                for each set item
            include_set_item_ref_paths [0, 1], default=0 - if 1, build ref paths for
                each set item returned

        returns: dict with key "sets"
            value: list of sets in the workspaces given by params
        """
        t1 = time.time()
        self._validate_list_params(params)

        workspace = params.get("workspace")
        workspaces = params.get("workspaces")
        include_metadata = params.get("include_metadata", 0)
        if not workspaces:
            workspaces = [str(workspace)]
        all_sets = self._list_all_sets(workspaces, include_metadata)
        t2 = time.time()
        all_sets = self._populate_set_refs(all_sets)

        # the top level sets list includes not just the set info, but
        # the list of obj refs contained in each of those sets
        top_level_sets = self._get_top_level_sets(all_sets)

        if params.get("include_set_item_info", 0) == 1:
            top_level_sets = self._populate_set_item_info(top_level_sets)

        if params.get("include_set_item_ref_paths", 0) == 1:
            top_level_sets = self._populate_set_item_ref_path(top_level_sets)

        if self.DEBUG:
            print(("Time of populate_sets: " + str(time.time() - t2)))
            print(("Total time of list_sets: " + str(time.time() - t1)))

        return {"sets": top_level_sets}

    def _validate_list_params(self: "GenericSetNavigator", params: dict[str, Any]) -> None:
        """Validates the parameters set to list_sets.

        Rules:
        1. At least one of workspace and workspaces must be present as keys. If
           both are missing, raise a ValueError
        2. include_set_item_info must be 0 or 1 if present.
        """
        if "workspace" not in params and "workspaces" not in params:
            msg = 'One of "workspace" or "workspaces" field required to list sets'
            raise ValueError(msg)

        if params.get("include_set_item_info", 0) not in [0, 1]:
            msg = '"include_set_item_info" field must be set to 0 or 1'
            raise ValueError(msg)

    def _list_all_sets(
        self: "GenericSetNavigator", workspaces: list[str], include_metadata: int
    ) -> list[dict[str, Any]]:
        """List all objects of one of the set_types in workspaces.

        :param workspaces: list of workspace IDs
        :type workspaces: list[str]
        :param include_metadata: whether or not to include metadata
        :type include_metadata: int (1 / 0)
        :return: list of objects in sets
        :rtype: list[dict]
        """
        ws_info_list = []
        t1 = time.time()
        if len(workspaces) == 1:
            # If just one workspaces, just fetch the one
            ws = workspaces[0]
            list_params = {}
            if str(ws).isdigit():
                list_params["id"] = int(ws)
            else:
                list_params["workspace"] = str(ws)
            ws_info_list.append(self.ws.get_workspace_info(list_params))
        else:
            # If > 1 workspace, it's faster to grab all workspaces the
            # user has access to and filter down to what's in the list
            ws_map = {key: True for key in workspaces}
            for ws_info in self.ws.list_workspace_info({"perm": "r"}):
                if ws_info[1] in ws_map or str(ws_info[0]) in ws_map:
                    ws_info_list.append(ws_info)
        if self.DEBUG:
            print(("Time of ws_info listing: " + str(time.time() - t1)))

        t2 = time.time()
        sets = []
        processed_refs = {}
        for t in GenericSetNavigator.SET_TYPES:
            list_params = {"includeMetadata": include_metadata, "type": t}
            for s in WorkspaceListObjectsIterator(
                self.ws, list_objects_params=list_params, ws_info_list=ws_info_list
            ):
                ref = self._build_obj_ref(s)
                sets.append({REF: ref, "info": s})
                processed_refs[ref] = True
        if self.DEBUG:
            print(("Time of object info listing: " + str(time.time() - t2)))
        return sets

    def _get_top_level_sets(self: "GenericSetNavigator", set_list):
        """Assumes set_list items are populated, kicks out any set that
        is directly referenced by another set on the list.

        set_list = list of dicts with keys
        ref - Workspace object reference

        """
        # create lookup hash for the sets
        set_ref_lookup = {}
        for s in set_list:
            set_ref_lookup[s[REF]] = 1

        # create a lookup to identify non-root sets
        sets_referenced_by_another_set = {}
        for s in set_list:
            for i in s["items"]:
                if i[REF] in set_ref_lookup:
                    sets_referenced_by_another_set[i[REF]] = 1

        # only add the sets that are root in this WS
        top_level_sets = []
        for s in set_list:
            if s[REF] in sets_referenced_by_another_set:
                continue
            top_level_sets.append(s)

        return top_level_sets

    def _populate_set_refs(
        self: "GenericSetNavigator", set_list: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Given a list of sets, go fetch their items and attach them to the original list.

        Has a side effect of updating the input set_list.

        set_list = list<dict> where each item has (at least) keys:
        * ref - Workspace object reference for the set object

        updates each item to have a key "items" containing a list
        of Workspace object references in no particular order.
        """
        if len(set_list) == 0:
            return []

        objects = [{REF: s[REF]} for s in set_list]
        obj_data = self.ws.get_objects2({"objects": objects, "no_data": 1})["data"]

        # if ws call worked, then len(obj_data)==len(set_list)
        for k in range(len(obj_data)):
            items = [{REF: item_ref} for item_ref in obj_data[k]["refs"]]
            set_list[k]["items"] = items

        return set_list

    def _populate_set_item_info(
        self: "GenericSetNavigator", set_list: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        # keys are refs to items, values are a ref to one of the
        # sets that they are in.  We build a lookup here first so that
        # we don't duplicate items in the ws call, but depending
        # on the set composition it may be cheaper to omit this
        # check and build the objects call directly with duplicates
        item_refs = {i[REF]: s[REF] for s in set_list for i in s["items"]}

        objects = [{REF: item_refs[ref] + ";" + ref} for ref in item_refs]

        if len(objects) > 0:
            obj_info_list = self.ws.get_object_info3({"objects": objects, "includeMetadata": 1})[
                "infos"
            ]
            # build info lookup
            item_info = {self._build_obj_ref(o): o for o in obj_info_list}

            for s in set_list:
                for item in s["items"]:
                    if item[REF] in item_info:
                        item["info"] = item_info[item[REF]]

        return set_list

    def _populate_set_item_ref_path(
        self: "GenericSetNavigator", set_list: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        for s in set_list:
            obj_spec = util.build_ws_obj_selector(s[REF], s.get("ref_path_to_set", []))
            util.populate_item_object_ref_paths(s["items"], obj_spec)

        return set_list

    def _build_obj_ref(self: "GenericSetNavigator", obj_info: list[str | Any]) -> str:
        return str(obj_info[6]) + "/" + str(obj_info[0]) + "/" + str(obj_info[4])

    def _get_ws_types(self: "GenericSetNavigator") -> list[str]:
        """Retrieve all the KBaseSet types available from the workspace.

        :param self: self
        :type self: self
        :raises ValueError: if there are no subtypes of KBaseSet
        :return: list of types
        :rtype: list[str]
        """
        set_type = "KBaseSets"
        module_info = self.ws.get_module_info({"mod": set_type})
        if not module_info:
            msg = "No KBaseSets modules found."
            raise ValueError(msg)

        all_types = []
        if "types" in module_info:
            for mod_type in module_info["types"]:
                mod_details = json.loads(module_info["types"][mod_type])
                if "id" in mod_details:
                    all_types.append(f"{set_type}.{mod_details.get('id')}")
                else:
                    msg = f"No id found in type description:\n{module_info['types'][mod_type]}"
                    raise ValueError(msg)

        self.ALL_SET_TYPES = all_types
        return all_types
