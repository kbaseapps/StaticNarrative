import os
import shutil
from ..narrative_ref import NarrativeRef


def upload_static_narrative(ref: NarrativeRef, narr_path: str,
                            upload_endpt: str, url_prefix: str = None) -> str:
    """
    Uploads a finished static Narrative to the display endpoint.
    Can raise:
        IOError if the path doesn't exist

    :param narr_id: int, the narrative id (will create url http://endpt/narr_id if it doesn't exist)
    :param narr_ver: int, the narrative version
    :param narr_path: str, the path to the generated static narrative html file
    :param upload_endpt: str, the URL where the file should be uploaded
        (could also be mounted path, we'll see?)
    :returns: The URL to the uploaded public, static, Narrative
    """
    # validate file is present
    # upload the file
    # return None
    if not os.path.exists(narr_path):
        raise IOError(f"Static Narrative doesn't seem to exist at path {narr_path}")

    # Let's assume we get an endpoint to copy to, so upload_endpt is a path
    # we need to:
    # 1. Make a directory there if it doesn't exist (/narr_id)
    # 2. Copy the file to /narr_id/index.html
    # 3. return the url
    static_narr_path = os.path.join(upload_endpt, str(ref.wsid), str(ref.ver))
    if not os.path.exists(static_narr_path):
        os.makedirs(static_narr_path)
    narr_dir = os.path.dirname(narr_path)
    shutil.copyfile(narr_path, os.path.join(static_narr_path, "index.html"))
    # shutil.copyfile(os.path.join(narr_dir, "dataBrowser.js"),
    #                 os.path.join(static_narr_path, "dataBrowser.js"))
    shutil.copyfile(os.path.join(narr_dir, "data.json"),
                    os.path.join(static_narr_path, "data.json"))

    static_url = url_prefix or ""
    return f"{static_url}/{ref.wsid}/{ref.ver}"
