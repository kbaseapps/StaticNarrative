import unittest
from StaticNarrative.exporter.exporter import NarrativeExporter


class ExporterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.token = "fake_token"
        cls.user_id = "fake_user"
        cls.ws_url = "https://fake_ws_url.com"

    def test_exporter_ok(self):
        exporter = NarrativeExporter(self.ws_url, self.user_id, self.token)
        url = exporter.export_narrative("123/45/6", "outfile.html")
