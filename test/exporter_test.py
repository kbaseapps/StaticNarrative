import unittest
from StaticNarrative.exporter.exporter import NarrativeExporter
import requests_mock
from configparser import ConfigParser
import os
from test.mocks import set_up_ok_mocks


class ExporterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_file = os.environ.get("KB_DEPLOYMENT_CONFIG", "test/deploy.cfg")
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items("StaticNarrative"):
            cls.cfg[nameval[0]] = nameval[1]
        cls.ws_url = cls.cfg["workspace-url"]
        cls.user_id = "some_user"
        cls.token = "some_token"

    @requests_mock.Mocker()
    def test_exporter_ok(self, rqm):
        ws_id = 43666
        ref_to_file = {
            "43666/1/18": "data/narrative-43666.1.18.json",
            "43666/3/1": "data/report-43666.3.1.json",
            "43666/7/1": "data/report-43666.7.1.json"
        }
        ref_to_info = {

        }
        ws_info = [
            43666,
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
            ws_id,
            ref_to_file,
            ref_to_info,
            ws_info,
            user_map
        )
        exporter = NarrativeExporter(self.cfg, self.user_id, self.token)
        static_path = exporter.export_narrative("43666/1/18", "outfile.html")
        self.assertEqual(static_path, os.path.join(self.cfg["scratch"], "outfile.html"))
