"""Uploads the generated static narrative to the static narrative server."""

import shutil
from pathlib import Path

from StaticNarrative.constants import OUTPUT_DATA_FILE, OUTPUT_HTML_FILE, SAVED_HTML_FILE
from StaticNarrative.narrative_ref import NarrativeRef


def upload_static_narrative(
    ref: NarrativeRef, dir_path: str | Path, upload_endpt: str | Path, url_prefix: str | None = None
) -> str:
    """Uploads a finished static Narrative to the display endpoint.

    :param ref: narrative ref object for the KBaseNarrative
    :param dir_path: str, the directory containing the generated html and JSON sidecar files
    :param upload_endpt: str, the URL where the file should be uploaded
        (could also be mounted path, we'll see?)
    :param url_prefix: str, prefix for paths to the index.html and data.json files
    :raises OSError: if the path doesn't exist
    :returns: The URL to the uploaded public, static, Narrative
    """
    # validate file is present and upload the file
    dir_path = Path(dir_path)
    if not dir_path.exists():
        msg = f"Static Narrative directory {dir_path} does not exist"
        raise OSError(msg)

    for f in [OUTPUT_HTML_FILE, OUTPUT_DATA_FILE]:
        file_path = dir_path / f
        if not file_path.exists():
            msg = f"Static Narrative file doesn't seem to exist at path {file_path}"
            raise OSError(msg)

    # Let's assume we get an endpoint to copy to, so upload_endpt is a path
    # we need to:
    # 1. Make a directory there if it doesn't exist (/narr_id)
    # 2. Copy the file to /narr_id/index.html
    # 3. return the url
    static_file_path = Path(upload_endpt) / str(ref.wsid) / str(ref.ver)
    static_file_path.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(dir_path / OUTPUT_HTML_FILE, static_file_path / SAVED_HTML_FILE)
    shutil.copyfile(dir_path / OUTPUT_DATA_FILE, static_file_path / OUTPUT_DATA_FILE)

    static_url = url_prefix or ""
    return f"{static_url}/{ref.wsid}/{ref.ver}/"
