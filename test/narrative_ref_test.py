import unittest

from StaticNarrative.narrative_ref import NarrativeRef


class NarrativeRefTestCase(unittest.TestCase):
    def test_ok(self):
        ref = NarrativeRef({"wsid": 123, "objid": 456, "ver": 7})
        self.assertEqual(ref.wsid, 123)
        self.assertEqual(ref.objid, 456)
        self.assertEqual(ref.ver, 7)

    def test_ok_from_parse(self):
        ref = NarrativeRef.parse("123/456/7")
        self.assertEqual(ref.wsid, 123)
        self.assertEqual(ref.objid, 456)
        self.assertEqual(ref.ver, 7)

    def test_init_fail(self):
        ok_ws_id = 1
        ok_obj_id = 2
        ok_ver = 3

        bad_ids = ["", None, "wat", [], {}, "-1", "4.5"]
        ws_id_err = "The Narrative Workspace id must be an integer > 0"
        obj_id_err = "The Narrative object id must be an integer > 0"
        ver_err = "The Narrative version must be an integer > 0"

        for _id in bad_ids:
            with self.assertRaises(ValueError) as e:
                NarrativeRef({"wsid": _id, "objid": ok_obj_id, "ver": ok_ver})
            self.assertIn(ws_id_err, str(e.exception))

            with self.assertRaises(ValueError) as e:
                NarrativeRef({"wsid": ok_ws_id, "objid": _id, "ver": ok_ver})
            self.assertIn(obj_id_err, str(e.exception))

            with self.assertRaises(ValueError) as e:
                NarrativeRef({"wsid": ok_ws_id, "objid": ok_obj_id, "ver": _id})
            self.assertIn(ver_err, str(e.exception))

    def test_parse_fail(self):
        bads = ["123/456", "123", "123/456/789/8", "123/456/", "123/", "foo/bar/baz"]
        for bad in bads:
            with self.assertRaises(ValueError):
                NarrativeRef.parse(bad)

    def test_equality(self):
        ref1 = NarrativeRef.parse("1/2/3")
        ref2 = NarrativeRef.parse("1/2/3")
        ref_ws = NarrativeRef.parse("4/2/3")
        ref_obj = NarrativeRef.parse("1/4/3")
        ref_ver = NarrativeRef.parse("1/2/4")

        self.assertEqual(ref1, ref1)
        self.assertEqual(ref1, ref2)
        self.assertEqual(ref2, ref1)
        self.assertNotEqual(ref1, ref_ws)
        self.assertNotEqual(ref1, ref_obj)
        self.assertNotEqual(ref1, ref_ver)
        self.assertNotEqual(ref_ws, ref1)
        self.assertNotEqual(ref_obj, ref1)
        self.assertNotEqual(ref_ver, ref1)
