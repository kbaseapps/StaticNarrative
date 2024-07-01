"""Uploads the generated static narrative to the static narrative server."""

import os
import shutil

from StaticNarrative.exporter.data_exporter import OUTPUT_DATA_FILE
from StaticNarrative.exporter.exporter import OUTPUT_HTML_FILE
from StaticNarrative.narrative_ref import NarrativeRef

SAVED_HTML_FILE = "index.html"


def upload_static_narrative(
    ref: NarrativeRef, dir_path: str, upload_endpt: str, url_prefix: str | None = None
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
    if not os.path.exists(dir_path):
        msg = f"Static Narrative directory {dir_path} does not exist"
        raise OSError(msg)

    for f in [OUTPUT_HTML_FILE, OUTPUT_DATA_FILE]:
        file_path = os.path.join(dir_path, f)
        if not os.path.exists(file_path):
            msg = f"Static Narrative file doesn't seem to exist at path {file_path}"
            raise OSError(msg)

    # Let's assume we get an endpoint to copy to, so upload_endpt is a path
    # we need to:
    # 1. Make a directory there if it doesn't exist (/narr_id)
    # 2. Copy the file to /narr_id/index.html
    # 3. return the url
    static_file_path = os.path.join(upload_endpt, str(ref.wsid), str(ref.ver))
    os.makedirs(static_file_path, exist_ok=True)
    narr_dir = os.path.dirname(file_path)
    shutil.copyfile(
        os.path.join(narr_dir, OUTPUT_HTML_FILE), os.path.join(static_file_path, SAVED_HTML_FILE)
    )
    shutil.copyfile(
        os.path.join(narr_dir, OUTPUT_DATA_FILE), os.path.join(static_file_path, OUTPUT_DATA_FILE)
    )

    static_url = url_prefix or ""
    return f"{static_url}/{ref.wsid}/{ref.ver}/"
