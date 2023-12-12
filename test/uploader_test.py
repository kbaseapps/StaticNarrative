"""Tests of the uploader module."""
import os

import pytest
from StaticNarrative.narrative_ref import NarrativeRef
from StaticNarrative.uploader.uploader import upload_static_narrative

REF = NarrativeRef.parse("1/2/3")


def test_upload_no_narrative_file() -> None:
    path = "not_a_path"
    with pytest.raises(
        IOError, match=f"Static Narrative doesn't seem to exist at path {path}"
    ):
        upload_static_narrative(REF, path, None)


def test_upload_need_to_make_path(scratch_dir: str) -> None:
    narr_file = os.path.join(scratch_dir, "test_file.html")
    with open(narr_file, "w") as fout:
        fout.write("test")

    upload_endpt = str(os.path.join(scratch_dir, "upload_test"))
    ret = upload_static_narrative(REF, narr_file, upload_endpt, None)

    assert f"/{REF.wsid}/{REF.ver}/" == ret
    assert os.path.exists(os.path.join(upload_endpt, str(REF.wsid), str(REF.ver)))
    assert os.path.isfile(
        os.path.join(upload_endpt, str(REF.wsid), str(REF.ver), "index.html")
    )
