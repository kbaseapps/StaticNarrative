from .processor_util import build_report_view_data
import re


class AppProcessor:
    def __init__(self, ws_url: str, token: str):
        self.ws_url = ws_url
        self.token = token

    def process(self, kb_info: dict, kb_meta: dict) -> dict:
        """
        Extracts the useful bits of the complicated metadata structure so that the Jinja
        templates don't look like spaghetti with stuff like
        'kbase.appCell.app.spec.info......'
        returns a dict with the updated info.
        """
        kb_info['app'] = {
            'title': kb_meta['attributes']['title'],
            'subtitle': kb_meta['attributes']['subtitle'],
            'version': kb_meta['appCell']['app']['version'],
            'id': kb_meta['appCell']['app']['id'],
            'tag': kb_meta['appCell']['app']['tag'],
            'catalog_url': kb_meta['attributes']['info']['url'],
        }
        kb_info["params"] = self._process_app_params(
            kb_meta["appCell"]["app"]["spec"]["parameters"],
            kb_meta["appCell"]["params"]
        )
        kb_info['output'] = {
            "widget": kb_meta['appCell'].get('exec', {}).get('outputWidgetInfo', {}),
            "result": kb_meta['appCell'].get('exec', {}).get('jobState', {}).get('result', []),
            "report": build_report_view_data(
                          self.ws_url, self.token,
                          kb_meta['appCell'].get('exec', {}).get('jobState', {}).get('result', [])
                      )
        }
        kb_info['job'] = {
            'state': "new, and hasn't been started."
        }
        if 'exec' in kb_meta['appCell']:
            kb_info['job']['state'] = self._get_job_state(kb_meta['appCell'])
        return kb_info

    def _process_app_params(self, spec_params: dict, param_values: dict) -> dict:
        """
        :param spec_params: the params dictionary from the stored app spec
        :param param_values: the parameter values dictionary, keyed on param ids
        :return: dictionary of input, output, and parameter lists
        """
        info = {
            "input": [],
            "output": [],
            "parameter": []
        }
        for p in spec_params:
            p["value"] = self._translate_param_value(param_values.get(p["id"]), p)
            p_type = p["ui_class"]
            info[p_type].append(p)
        return info

    def _translate_param_value(self, value, param_spec: dict):
        """
        Overall flow.
        1. if value is a list, iterate everything below over it.
        2. inspect the spec to see what the value represents.
            a. if a
        2. if value is a string, check if its an UPA, verify with the spec that it
            should be an object
        3. if value is an int... stuff.
        """
        # if param_spec.text_options.valid_ws_types exists and has entries, then its an object input
        # test if value is an UPA and translate it to get its original object name.

        # types:
        field_type = param_spec["field_type"]
        if field_type == "text":
            valid_ws_types = param_spec.get("text_options", {}).get("valid_ws_types", [])
            if len(valid_ws_types) > 0 and value:
                if isinstance(value, list):
                    value = [self._interpret_ws_obj_input(v) for v in value]
                else:
                    value = self._interpret_ws_obj_input(value)
        return value

    def _interpret_ws_obj_input(self, value: str) -> str:
        """
        If value is an UPA, translate into workspace object names
        """
        if self._is_upa(value):
            return

    def _is_upa(self, s: str) -> bool:
        """
        An UPA matches this structure: ##/##/##
        E.g. 123/456/789
        """
        upa_regex = r"^\d+\/\d+\/\d+$"
        return re.match(upa_regex, s) is not None

    def _get_job_state(self, app_meta: dict) -> str:
        job_state = app_meta['exec'].get('jobState', {})
        state = job_state.get('job_state', job_state.get('status', 'unknown'))
        if isinstance(state, list):
            state = state[1]
        return state
