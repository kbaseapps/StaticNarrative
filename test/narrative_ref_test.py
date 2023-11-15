import unittest

import pytest
from StaticNarrative.narrative_ref import NarrativeRef

WSID = 123
OBJID = 456
VER = 7

WS_ID_ERR = "The Narrative workspace ID must be an integer > 0"
OBJ_ID_ERR = "The Narrative object ID must be an integer > 0"
VER_ERR = "The Narrative version must be an integer > 0"


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

        bad_ids = ["", None, "wat", [], {}, "-1", "4.5", 0]

        for bad_id in bad_ids:
            with pytest.raises(ValueError, match=WS_ID_ERR):
                NarrativeRef({"wsid": bad_id, "objid": ok_obj_id, "ver": ok_ver})

            with pytest.raises(ValueError, match=OBJ_ID_ERR):
                NarrativeRef({"wsid": ok_ws_id, "objid": bad_id, "ver": ok_ver})

            with pytest.raises(ValueError, match=VER_ERR):
                NarrativeRef({"wsid": ok_ws_id, "objid": ok_obj_id, "ver": bad_id})


    def test_parse_fail(self) -> None:
        # incorrect number of slashes
        bad_refs = ["123", "123/456", "123/456/789/8"]
        for bad in bad_refs:
            with pytest.raises(ValueError, match="A Narrative ref must be of the format wsid/objid/ver"):
                NarrativeRef.parse(bad)

        # slashes without numbers
        with pytest.raises(ValueError, match=VER_ERR):
            NarrativeRef.parse("123/456/")

        with pytest.raises(ValueError, match=OBJ_ID_ERR):
            NarrativeRef.parse("123//456")

        with pytest.raises(ValueError, match=OBJ_ID_ERR):
            NarrativeRef.parse("123//")

        with pytest.raises(ValueError, match=WS_ID_ERR):
            NarrativeRef.parse("/123/456")

        with pytest.raises(ValueError, match=WS_ID_ERR):
            NarrativeRef.parse("//123")

        with pytest.raises(ValueError, match=WS_ID_ERR):
            NarrativeRef.parse("/123/")

        # invalid data type
        with pytest.raises(ValueError, match=WS_ID_ERR):
            NarrativeRef.parse("foo/bar/baz")

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
