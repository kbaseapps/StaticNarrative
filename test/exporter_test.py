import unittest
from StaticNarrative.exporter.exporter import NarrativeExporter
import requests_mock
import os
from test.mocks import set_up_ok_mocks
from StaticNarrative.narrative_ref import NarrativeRef
from test.test_config import get_test_config


class ExporterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = get_test_config()
        cls.user_id = "some_user"
        cls.token = "some_token"

    @requests_mock.Mocker()
    def test_exporter_ok(self, rqm):
        ws_id = 43666
        ref_to_file = {
            "43666/1/21": "data/43666/narrative-43666.1.21.json",
            "43666/1/18": "data/43666/narrative-43666.1.18.json",
            "43666/3/1": "data/43666/report-43666.3.1.json",
            "43666/7/1": "data/43666/report-43666.7.1.json"
        }
        ref_to_info = {

        }
        ws_info = [
            ws_id,
            'some_narrative',
            self.user_id,
            '2019-08-26T17:33:56+0000',
            7,
            'a',
            'r',
            'unlocked',
            {
                'cell_count': '1',
                'narrative_nice_name': 'Test Exporting',
                'searchtags': 'narrative',
                'is_temporary': 'false',
                'narrative': '1'
            }
        ]
        user_map = {self.user_id: "Some User"}

        set_up_ok_mocks(
            rqm,
            ref_to_file=ref_to_file,
            ref_to_info=ref_to_info,
            ws_info=ws_info,
            user_map=user_map,
            ws_obj_info_file="data/43666/objects-43666.json"
        )
        exporter = NarrativeExporter(self.cfg, self.user_id, self.token)
        static_path = exporter.export_narrative(
            NarrativeRef({"wsid": ws_id, "objid": 1, "ver": 21}),
            self.cfg["scratch"]
        )
        self.assertEqual(static_path, os.path.join(self.cfg["scratch"], "narrative.html"))
