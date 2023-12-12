"""Class for fetching objects from the workspace."""
from collections import deque

from installed_clients.WorkspaceClient import Workspace


class WorkspaceListObjectsIterator:
    # ws_info - optional workspace info tuple (if is not defined then either ws_id
    #    or ws_name should be provided),
    # ws_id/ws_name - optional workspace identification (if neither is defined
    #    then ws_info should be provided),
    # list_objects_params - optional structure with such Woskspace.ListObjectsParams
    #    as 'type' or 'before', 'after', 'showHidden', 'includeMetadata' and so on,
    #    wherein there is no need to set 'ids' or 'workspaces' or 'min/maxObjectID'.
    def __init__(
        self: "WorkspaceListObjectsIterator",
        ws_client: Workspace,
        ws_info_list=None,
        ws_id=None,
        ws_name=None,
        list_objects_params=None,
        part_size=10000,
        global_limit=100000,
    ) -> None:
        if not list_objects_params:
            list_objects_params = {}
        self.ws_client = ws_client
        if ws_info_list is None:
            if ws_id is None and ws_name is None:
                raise ValueError(
                    "In case ws_info_list is not set either ws_id or ws_name should be set"
                )
            ws_info_list = [
                self.ws_client.get_workspace_info({"id": ws_id, "workspace": ws_name})
            ]
        # Let's split workspaces into blocks
        blocks = []  # Each block is array of ws_info
        sorted_ws_info_deque = deque(sorted(ws_info_list, key=lambda x: x[4]))
        while sorted_ws_info_deque:
            block_size = 0
            block = []
            while sorted_ws_info_deque:
                item = sorted_ws_info_deque.popleft()
                if len(block) == 0 or block_size + item[4] <= part_size:
                    block.append(item)
                    block_size += item[4]
                else:
                    sorted_ws_info_deque.appendleft(item)
                    break
            blocks.append(block)
        self.block_iter = blocks.__iter__()
        self.list_objects_params = list_objects_params
        self.min_obj_id = -1
        self.max_obj_count = -1
        self.part_size = part_size
        self.global_limit = global_limit
        self.total_counter = 0
        self.part_iter = self._load_next_part()

    # iterator implementation
    def __iter__(
        self: "WorkspaceListObjectsIterator",
    ) -> "WorkspaceListObjectsIterator":
        return self

    def __next__(
        self: "WorkspaceListObjectsIterator",
    ):
        while self.part_iter is not None:
            try:
                self.total_counter += 1
                if (
                    self.global_limit is not None
                    and self.total_counter > self.global_limit
                ):
                    raise StopIteration
                return next(self.part_iter)
            except StopIteration:
                self.part_iter = self._load_next_part()
        raise StopIteration

    def _load_next_part(
        self: "WorkspaceListObjectsIterator",
    ) -> "WorkspaceListObjectsIterator":
        if self.min_obj_id < 0 or self.min_obj_id > self.max_obj_count:
            try:
                block = next(self.block_iter)
                self.list_objects_params["ids"] = [ws_info[0] for ws_info in block]
            except StopIteration:
                return None
            last_ws_info = block[len(block) - 1]
            self.min_obj_id = 1
            self.max_obj_count = last_ws_info[4]
        max_obj_id = self.min_obj_id + self.part_size - 1
        self.list_objects_params["minObjectID"] = self.min_obj_id
        self.list_objects_params["maxObjectID"] = max_obj_id
        self.min_obj_id += self.part_size  # For next load cycle
        ret = self.ws_client.list_objects(self.list_objects_params)
        return ret.__iter__()
