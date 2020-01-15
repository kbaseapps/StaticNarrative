import os
import unittest
from StaticNarrative.uploader.uploader import upload_static_narrative
from StaticNarrative.narrative_ref import NarrativeRef
from .test_config import get_test_config


class UploaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = NarrativeRef.parse("1/2/3")
        cls.cfg = get_test_config()

    def test_upload_no_narrative_file(self):
        path = "not_a_path"
        with self.assertRaises(IOError) as e:
            upload_static_narrative(self.ref, path, None)
        self.assertIn(f"Static Narrative doesn't seem to exist at path {path}", str(e.exception))

    def test_upload_need_to_make_path(self):
        narr_file = os.path.join(self.cfg["scratch"], "test_file.html")
        with open(narr_file, "w") as fout:
            fout.write("test")
        upload_endpt = str(os.path.join(self.cfg["scratch"], "upload_test"))
        ret = upload_static_narrative(self.ref, narr_file, upload_endpt, None)
        self.assertEqual(f"/{self.ref.wsid}/{self.ref.ver}", ret)
        self.assertTrue(
            os.path.exists(
                os.path.join(upload_endpt, str(self.ref.wsid), str(self.ref.ver))))
        self.assertTrue(
            os.path.isfile(
                os.path.join(upload_endpt, str(self.ref.wsid), str(self.ref.ver), "index.html")
            )
        )
