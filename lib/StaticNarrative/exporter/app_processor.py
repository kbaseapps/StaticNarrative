import math
import re
from typing import T

from installed_clients.WorkspaceClient import Workspace

from .processor_util import build_report_view_data


class AppProcessor:
    def __init__(
        self: "AppProcessor", host: str, ws_url: str, nms_url: str, token: str
    ) -> None:
        self.host = host
        self.ws_url = ws_url
        self.nms_url = nms_url
        self.token = token

    def process(
        self: "AppProcessor", kb_info: dict[str, T], kb_meta: dict[str, T]
    ) -> dict[str, T]:
        """
        Extracts the useful bits of the complicated metadata structure so that the Jinja
        templates don't look like spaghetti with stuff like
        'kbase.appCell.app.spec.info......'
        returns a dict with the updated info.
        """
        kb_info["app"] = {
            "title": kb_meta["attributes"]["title"],
            "subtitle": kb_meta["attributes"]["subtitle"],
            "version": kb_meta["appCell"]["app"]["version"],
            "id": kb_meta["appCell"]["app"]["id"],
            "tag": kb_meta["appCell"]["app"]["tag"],
            "catalog_url": kb_meta["attributes"]["info"]["url"],
        }
        kb_info["params"] = self._process_app_params(
            kb_meta["appCell"]["app"]["spec"]["parameters"],
            kb_meta["appCell"]["params"],
        )
        exec_state = kb_meta["appCell"].get("exec", {})
        exec_result = []
        job_state = exec_state.get("jobState", {})
        if "result" in job_state:  # NJS (aka EE1)
            exec_result = job_state["result"]
        elif "job_output" in job_state:  # EE2
            exec_result = job_state["job_output"].get("result")

        ws_client = Workspace(self.ws_url, token=self.token)
        kb_info["output"] = {
            "widget": exec_state.get("outputWidgetInfo", {}),
            "result": exec_result,
            "report": build_report_view_data(self.host, ws_client, exec_result),
        }
        kb_info["job"] = {"state": "This app is new, and hasn't been started."}
        if "exec" in kb_meta["appCell"]:
            kb_info["job"]["state"] = self._get_job_state(kb_meta["appCell"])
        return kb_info

    def _process_app_params(
        self: "AppProcessor", spec_params: dict[str, T], param_values: dict[str, T]
    ) -> dict[str, list]:
        """
        :param spec_params: the params dictionary from the stored app spec
        :param param_values: the parameter values dictionary, keyed on param ids
        :return: dictionary of input, output, and parameter lists
        """
        info = {"input": [], "output": [], "parameter": []}

        # two passes
        # 1. Make a lookup table for UPA -> object info
        upas = {}
        for p in spec_params:
            upas.update(self._make_upa_dict(param_values.get(p["id"]), p))

        # 2. Do translation from internal value -> something prettier.
        for p in spec_params:
            p["value"] = self._translate_param_value(param_values.get(p["id"]), p, upas)
            p_type = p["ui_class"]
            info[p_type].append(p)
        return info

    def _make_upa_dict(
        self: "AppProcessor", value: T, param_spec: dict[str, T]
    ) -> dict[str, T]:
        upas = []
        if param_spec["field_type"] == "text":
            valid_ws_types = param_spec.get("text_options", {}).get(
                "valid_ws_types", []
            )
            if len(valid_ws_types) > 0 and value:
                if isinstance(value, list):
                    for v in value:
                        if self._is_upa(v):
                            upas.append(v)
                elif self._is_upa(value):
                    upas.append(value)
        upa_map = {}
        if len(upas):
            ws_client = Workspace(url=self.ws_url, token=self.token)
            obj_infos = ws_client.get_object_info3(
                {"objects": [{"ref": upa} for upa in upas]}
            )["infos"]
            upa_map = {u: obj_infos[i] for i, u in enumerate(upas)}
        return upa_map

    def _translate_param_value(
        self: "AppProcessor",
        value: None | int | str | list,
        param_spec: dict[str, T],
        upas: dict[str, T],
    ):
        """
        Overall flow.
        1. if value is a list, iterate everything below over it.
        2. inspect the spec to see what the value represents.
            a. if a
        2. if value is a string, check if its an UPA, verify with the spec that it
            should be an object
        3. if value is an int... stuff.
        """
        # if param_spec.text_options.valid_ws_types exists and has entries,
        # it's an object input
        # test if value is an UPA and translate it to get its original object name.

        # types:
        field_type = param_spec["field_type"]
        if field_type == "text":
            valid_ws_types = param_spec.get("text_options", {}).get(
                "valid_ws_types", []
            )
            if len(valid_ws_types) > 0 and value:
                if isinstance(value, list):
                    value = [upas[v][1] if v in upas else v for v in value]
                else:
                    value = upas[value][1] if value in upas else value
        return value

    def _is_upa(self: "AppProcessor", s: str) -> bool:
        """
        An UPA matches this structure: ##/##/##
        E.g. 123/456/789
        """
        upa_regex = r"^\d+\/\d+\/\d+$"
        return re.match(upa_regex, s) is not None

    def _get_job_state(self: "AppProcessor", app_meta: dict[str, T]) -> str:
        """
        Returns the job state as a readable string.
        One of:
        "completed without errors in TTT"
        "completed with errors in TTT"
        "canceled"
        "queued and not run"
        """

        # Step 1, get job state
        job_state = app_meta["exec"].get("jobState", {})
        state = job_state.get("job_state", job_state.get("status", "unknown"))
        if isinstance(state, list):
            state = state[1]

        # support NJS_Wrapper's "suspend" state
        if state == "suspend":
            if job_state.get("error"):
                state = "error"
            elif job_state.get("cancelled") or job_state.get("canceled"):
                state = "canceled"

        if state in ["canceled", "cancelled", "terminated"]:
            return "This app was canceled before completion."

        # Step 2, get runtime.
        # runtime is calculated as either:
        # (ee2) 'finished - running' or
        # (njs) 'finish_time - exec_start_time'
        runtime = None
        # njs
        if "finish_time" in job_state and "exec_start_time" in job_state:
            runtime = self._ms_to_readable(
                job_state["finish_time"] - job_state["exec_start_time"]
            )
        # ee2
        elif "finished" in job_state and "running" in job_state:
            runtime = self._ms_to_readable(job_state["finished"] - job_state["running"])

        if state in ["estimating", "running", "in-progress"]:
            return_state = "This app is still in progress"
            if runtime:
                return_state = f"{return_state}, and has been running for {runtime}."
        elif state in ["completed", "finished"]:
            return_state = "This app completed without errors"
            if runtime:
                return_state = f"{return_state} in {runtime}"
        else:
            return_state = "This app produced errors"
            if runtime:
                return_state = f"{return_state} in {runtime}"

        return return_state + "."

    def _ms_to_readable(self: "AppProcessor", ms: int) -> str | None:
        """
        Converts number of milliseconds to a human readable string with format Wd Xh Ym Zs
        e.g. 1234567ms => "
        """
        # simply make sure it's a number
        try:
            ms = int(ms)
        except Exception:
            return None
        days = 86400000
        hours = 3600000
        minutes = 60000
        seconds = 1000
        d = math.floor(ms / days)
        r = ms % days
        h = math.floor(r / hours)
        r = r % hours
        m = math.floor(r / minutes)
        r = r % minutes
        s = round(r / seconds)

        t = []
        used_h = False
        if d > 0:
            t.append(f"{d}d")
        if h > 0 or d > 0:
            t.append(f"{h}h")
            used_h = True
        if m > 0 or used_h:
            t.append(f"{m}m")
        t.append(f"{s}s")
        return " ".join(t)
