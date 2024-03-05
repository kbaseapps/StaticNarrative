"""Test the narrative_ref module."""

from typing import Any

import pytest
from StaticNarrative.narrative_ref import NarrativeRef

WSID = 123
OBJID = 456
VER = 7

WS_FORMAT_ERR = "A Narrative ref must be of the format wsid/objid/ver"
WS_ID_ERR = "The Narrative workspace ID must be an integer > 0"
OBJ_ID_ERR = "The Narrative object ID must be an integer > 0"
VER_ERR = "The Narrative version must be an integer > 0"


def test_ok() -> None:
    ref = NarrativeRef({"wsid": WSID, "objid": OBJID, "ver": VER})
    assert ref.wsid == WSID
    assert ref.objid == OBJID
    assert ref.ver == VER


def test_ok_from_parse() -> None:
    ref = NarrativeRef.parse("123/456/7")
    assert ref.wsid == WSID
    assert ref.objid == OBJID
    assert ref.ver == VER


@pytest.mark.parametrize("bad_id", ["", None, "wat", [], {}, "-1", "4.5", 0])
@pytest.mark.parametrize(
    "args",
    [
        pytest.param(
            {
                "bad_id": arr[0],
                "error": arr[1],
            },
            id=arr[1],
        )
        for arr in [["wsid", WS_ID_ERR], ["objid", OBJ_ID_ERR], ["ver", VER_ERR]]
    ],
)
def test_init_fail(
    bad_id: list[object] | dict[Any, Any] | str | None, args: dict[str, Any]
) -> None:
    params = {"wsid": WSID, "objid": OBJID, "ver": VER}
    # replace the OK version of the param denoted by args["bad_id"] with the bad_id
    del params[args["bad_id"]]
    params[args["bad_id"]] = bad_id

    with pytest.raises(ValueError, match=args["error"]):
        NarrativeRef(params)


errors = {
    WS_FORMAT_ERR: ["123", "123/456", "123/456/789/8"],
    VER_ERR: ["123/456/"],
    OBJ_ID_ERR: ["123//456", "123//"],
    WS_ID_ERR: ["/123/456", "//123", "/123/", "foo/bar/baz"],
}


@pytest.mark.parametrize(
    "args",
    [
        pytest.param({"input": value, "err": key}, id=value)
        for key, value_list in errors.items()
        for value in value_list
    ],
)
def test_parse_fail(args: dict[str, str]) -> None:
    with pytest.raises(ValueError, match=args["err"]):
        NarrativeRef.parse(args["input"])


def test_equality() -> None:
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
