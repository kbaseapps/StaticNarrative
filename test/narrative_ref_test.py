import unittest

import pytest
from StaticNarrative.narrative_ref import NarrativeRef

WSID = 123
OBJID = 456
VER = 7

class NarrativeRefTestCase(unittest.TestCase):
    def test_ok(self) -> None:
        ref = NarrativeRef({"wsid": WSID, "objid": OBJID, "ver": VER})
        assert ref.wsid == WSID
        assert ref.objid == OBJID
        assert ref.ver == VER

    def test_ok_from_parse(self) -> None:
        ref = NarrativeRef.parse("123/456/7")
        assert ref.wsid == WSID
        assert ref.objid == OBJID
        assert ref.ver == VER

    def test_init_fail(self) -> None:
        ok_ws_id = 1
        ok_obj_id = 2
        ok_ver = 3

        bad_ids = ["", None, "wat", [], {}, "-1", "4.5"]
        ws_id_err = "The Narrative workspace ID must be an integer > 0"
        obj_id_err = "The Narrative object ID must be an integer > 0"
        ver_err = "The Narrative version must be an integer > 0"

        for bad_id in bad_ids:
            with pytest.raises(ValueError, match=ws_id_err):
                NarrativeRef({"wsid": bad_id, "objid": ok_obj_id, "ver": ok_ver})

            with pytest.raises(ValueError, match=obj_id_err):
                NarrativeRef({"wsid": ok_ws_id, "objid": bad_id, "ver": ok_ver})

            with pytest.raises(ValueError, match=ver_err):
                NarrativeRef({"wsid": ok_ws_id, "objid": ok_obj_id, "ver": bad_id})

    def test_parse_fail(self) -> None:
        bads = ["123/456", "123", "123/456/789/8", "123/456/", "123/", "foo/bar/baz"]
        for bad in bads:
            with pytest.raises(ValueError):
                NarrativeRef.parse(bad)

    def test_equality(self) -> None:
        ref1 = NarrativeRef.parse("1/2/3")
        ref2 = NarrativeRef.parse("1/2/3")
        ref_ws = NarrativeRef.parse("4/2/3")
        ref_obj = NarrativeRef.parse("1/4/3")
        ref_ver = NarrativeRef.parse("1/2/4")

        assert ref1 == ref2
        assert ref2 == ref1
        assert ref1 != ref_ws
        assert ref1 != ref_obj
        assert ref1 != ref_ver
        assert ref_ws != ref1
        assert ref_obj != ref1
        assert ref_ver != ref1
