"""Tests of the uploader module."""

import os
from pathlib import Path

import pytest
from _pytest._py.path import LocalPath
from StaticNarrative.exporter.data_exporter import OUTPUT_DATA_FILE
from StaticNarrative.exporter.exporter import OUTPUT_HTML_FILE
from StaticNarrative.narrative_ref import NarrativeRef
from StaticNarrative.uploader.uploader import SAVED_HTML_FILE, upload_static_narrative

REF = NarrativeRef.parse("1/2/3")


def test_upload_no_directory() -> None:
    fake_path = "not/a/real/path"
    with pytest.raises(IOError, match=f"Static Narrative directory {fake_path} does not exist"):
        upload_static_narrative(REF, fake_path, "/some/path")


def test_upload_no_narrative_file(tmpdir: LocalPath) -> None:
    path = Path(tmpdir) / OUTPUT_HTML_FILE
    with pytest.raises(
        IOError, match=f"Static Narrative file doesn't seem to exist at path {path}"
    ):
        upload_static_narrative(REF, str(tmpdir), "/some/path")


def test_upload_no_data_json_file(tmpdir: LocalPath) -> None:
    narr_file = Path(tmpdir) / OUTPUT_HTML_FILE
    with open(narr_file, "w") as fout:
        fout.write("test")

    path = Path(tmpdir) / OUTPUT_DATA_FILE
    with pytest.raises(
        IOError, match=f"Static Narrative file doesn't seem to exist at path {path}"
    ):
        upload_static_narrative(REF, str(tmpdir), "/some/path", None)


def test_upload_need_to_make_path(tmpdir: LocalPath) -> None:
    narr_file = Path(tmpdir) / OUTPUT_HTML_FILE
    data_file = Path(tmpdir) / OUTPUT_DATA_FILE

    for f in [narr_file, data_file]:
        with open(f, "w") as fout:
            fout.write("test")

    upload_endpt = str(Path(tmpdir) / "some" / "dirs" / "upload_test")
    ret = upload_static_narrative(REF, tmpdir, str(upload_endpt))

    assert f"/{REF.wsid}/{REF.ver}/" == ret
    assert os.path.exists(os.path.join(upload_endpt, str(REF.wsid), str(REF.ver)))
    assert os.path.isfile(os.path.join(upload_endpt, str(REF.wsid), str(REF.ver), SAVED_HTML_FILE))
    assert os.path.isfile(os.path.join(upload_endpt, str(REF.wsid), str(REF.ver), OUTPUT_DATA_FILE))
