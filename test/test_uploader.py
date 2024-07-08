"""Tests of the uploader module."""

from pathlib import Path

import pytest
from StaticNarrative.constants import OUTPUT_DATA_FILE, OUTPUT_HTML_FILE, SAVED_HTML_FILE
from StaticNarrative.narrative_ref import NarrativeRef
from StaticNarrative.uploader.uploader import upload_static_narrative

REF = NarrativeRef.parse("1/2/3")


@pytest.mark.parametrize("path_type", [str, Path])
def test_upload_no_directory(path_type: type[str] | type[Path]) -> None:
    """Test that an error is raised if the directory that the SN files are in does not exist."""
    fake_path = "not/a/real/path"
    with pytest.raises(IOError, match=f"Static Narrative directory {fake_path} does not exist"):
        upload_static_narrative(REF, path_type(fake_path), "/some/path")


@pytest.mark.parametrize("path_type", [str, Path])
def test_upload_no_narrative_file(tmp_path: Path, path_type: type[str] | type[Path]) -> None:
    """Test that an error is raised if the narrative HTML file does not exist."""
    path = tmp_path / OUTPUT_HTML_FILE
    with pytest.raises(
        IOError, match=f"Static Narrative file doesn't seem to exist at path {path}"
    ):
        upload_static_narrative(REF, path_type(tmp_path), "/some/path")


@pytest.mark.parametrize("path_type", [str, Path])
def test_upload_no_data_json_file(tmp_path: Path, path_type: type[str] | type[Path]) -> None:
    """Test that an error is raised if the data.json file does not exist."""
    narr_file = tmp_path / OUTPUT_HTML_FILE
    narr_file.touch()

    path = tmp_path / OUTPUT_DATA_FILE
    with pytest.raises(
        IOError, match=f"Static Narrative file doesn't seem to exist at path {path}"
    ):
        upload_static_narrative(REF, path_type(tmp_path), "/some/path", None)


@pytest.mark.parametrize("endpoint_type", [str, Path])
@pytest.mark.parametrize("path_type", [str, Path])
def test_upload_need_to_make_path(
    tmp_path: Path, path_type: type[str] | type[Path], endpoint_type: type[str] | type[Path]
) -> None:
    """Test that a new directory is created if the output directory does not exist."""
    narr_file = tmp_path / OUTPUT_HTML_FILE
    data_file = tmp_path / OUTPUT_DATA_FILE
    wsid = str(REF.wsid)
    ver = str(REF.ver)

    for f in [narr_file, data_file]:
        f.touch()

    upload_endpt = tmp_path / "some" / "dirs" / "upload_test"
    ret = upload_static_narrative(REF, path_type(tmp_path), endpoint_type(upload_endpt))

    assert f"/{REF.wsid}/{REF.ver}/" == ret
    assert Path(upload_endpt / wsid / ver).exists()
    assert Path(upload_endpt / wsid / ver / SAVED_HTML_FILE).is_file()
    assert Path(upload_endpt / wsid / ver / OUTPUT_DATA_FILE).is_file()
