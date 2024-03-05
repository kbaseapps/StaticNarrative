"""Some utility functions for handling Narratives and permissions."""
import logging
import re
import time
from typing import Any

from dateutil import parser as date_parser
from installed_clients.baseclient import ServerError
from installed_clients.WorkspaceClient import Workspace

from StaticNarrative.exceptions import WorkspaceError
from StaticNarrative.narrative_ref import NarrativeRef

NARRATIVE_TYPE = "KBaseNarrative.Narrative"
TYPE_REGEX = rf"^{NARRATIVE_TYPE}-\d+\.\d+$"


def read_narrative(ref: NarrativeRef, ws_client: Workspace) -> dict[str, Any]:
    """Fetches a Narrative and its object info from the Workspace.

    If content is False, this only returns the Narrative's info
    and metadata, otherwise, it returns the whole workspace object.

    This is mainly a wrapper around Workspace.get_objects2(), except that
    it always returns a dict. If content is False, it returns a dict
    containing a single key: 'info', with the object info and, optionally,
    metadata.

    Can the following errors:
        ValueError (if ref isn't a Narrative object),
        WorkspaceError if there's a Workspace issue (ref isn't valid, or token isn't valid)

    :param ref: a NarrativeRef
    :param content: if True, returns the narrative document, otherwise just the metadata
    :param include_metadata: if True, includes the object metadata when returning
    """
    try:
        narr_data = ws_client.get_objects2({"objects": [{"ref": str(ref)}]})
        nar = narr_data["data"][0]
        _validate_narr_type(nar["info"][2], ref)
        return nar["data"]
    except ServerError as err:
        raise WorkspaceError(err, ref.wsid) from err


def _validate_narr_type(t: str, ref: NarrativeRef) -> None:
    """Validates the given string to ensure it is a KBase Narrative type string.

    Checks that the string of the form "KBaseNarrative.Narrative-1.0", including the version.
    If it's not, or if it's not a string, a ValueError is raised.

    :param t: str - the type string to compare
    :param ref: NarrativeRef - the narrative reference that t came from (used in error reporting)
    """
    if not isinstance(t, str):
        msg = "The type string must be a string"
        raise TypeError(msg)

    if not re.match(TYPE_REGEX, t):
        err = "Expected a Narrative object"
        if ref is not None:
            err += f" with reference {ref}"
        err += f", got a {t}"
        raise ValueError(err)


def save_narrative_url(ws_url: str, token: str, ref: NarrativeRef, url: str) -> None:
    """Updates the Narrative workspace metadata with info about the new Static Narrative.

    Creates (or updates) metadata keys:
    static_narrative: narrative url
    static_narrative_ver: int, the version
    static_narrative_saved: int, ms since epoch saved
    If it fails, will throw a WorkspaceError
    :param ws_url: str - the URL for the workspace endpoint
    :param token: str - the user's auth token
    :param ref: the NarrativeRef for the Narrative that was made static
    :param url: the url string that was saved (should really just be the path, not the full url,
        something like /123/4 instead of ci.kbase.us/n/123/4)
    """
    new_meta = {
        "static_narrative": url,
        "static_narrative_ver": str(ref.ver),
        "static_narrative_saved": str(int(time.time() * 1000)),
    }
    ws_client = Workspace(url=ws_url, token=token)
    try:
        ws_client.alter_workspace_metadata({"wsi": {"id": ref.wsid}, "new": new_meta})
    except ServerError as err:
        raise WorkspaceError(err, ref.wsid) from err


def get_static_info(ws_url: str, token: str, ws_id: int) -> dict[str, int | str]:
    """Looks up the static narrative info for the given workspace ID.

    That info is stashed in the Workspace metadata, so that gets fetched, munged into a structure,
    and returned.
    If there's no static narrative, this returns an empty structure, as there's no info.
    If ws_id is not present, or not numeric, raises a ValueError.
    If there's a problem when contacting the Workspace (anything that raises a ServerError),
    this raises a WorkspaceError.
    :param ws_url: the URL for the workspace endpoint
    :param token: the user auth token
    :param ws_id: the workspace id of the narrative to fetch info for.
    :returns: a dictionary with the following keys if a static narrative is present:
        ws_id - int - the workspace id
        narrative_id - int - the id of the narrative object
        version - int - the version of the narrative object made static
        url - str - the url of the static narrative
        narr_saved - int - the timestamp of when the narrative that the static version is
            based on was saved (ms since epoch)
        static_saved - int - the timestamp of when the static narrative was saved (ms
            since epoch)

    """
    if not ws_id or not str(ws_id).isdigit():
        msg = f"The parameter ws_id must be an integer, not {ws_id}"
        raise ValueError(msg)

    ws_client = Workspace(url=ws_url, token=token)
    try:
        ws_info = ws_client.get_workspace_info({"id": ws_id})
    except ServerError as err:
        raise WorkspaceError(err, ws_id) from err

    info = {}
    ws_meta = ws_info[8]
    if "static_narrative_ver" in ws_meta:
        info = {
            "ws_id": ws_id,
            "version": int(ws_meta["static_narrative_ver"]),
            "narrative_id": int(ws_meta["narrative"]),
            "url": ws_meta["static_narrative"],
            "static_saved": int(ws_meta["static_narrative_saved"]),
        }
        try:
            obj_info = ws_client.get_object_info3(
                {
                    "objects": [
                        {"ref": f"{ws_id}/{info['narrative_id']}/{info['version']}"}
                    ]
                }
            )
        except ServerError as err:
            raise WorkspaceError(err, ws_id) from err
        ts = date_parser.isoparse(obj_info["infos"][0][3]).timestamp()
        info["narr_saved"] = int(ts * 1000)
    return info


def verify_admin_privilege(
    workspace_url: str, user_id: str, token: str, ws_id: int
) -> None:
    """Ensures that the user has admin permissions for the workspace.

    Raises PermissionError if the user is not an admin (has 'a' rights) on the Workspace.
    Gotta write to the Workspace metadata to create and save a Static Narrative, so this
    checks that the user has rights.
    If the user has admin rights, this returns None.

    Raises a WorkspaceError if anything goes wrong with the permission lookup.

    :param workspace_url: str - the workspace endpoint url
    :param token: str - the auth token
    :param user_id: str - the user id to check. This is expected to be the owner of the
        provided token. Not checked, though, since that should be done by the Server module.
    :param ws_id: int - the workspace to check
    """
    ws_client = Workspace(url=workspace_url, token=token)
    try:
        perms = ws_client.get_permissions({"id": ws_id})
    except ServerError as err:
        raise WorkspaceError(err, ws_id) from err
    if user_id not in perms or perms[user_id] != "a":
        err = f"User {user_id} does not have admin rights on workspace {ws_id}"
        logging.getLogger("StaticNarrative").error(err)
        raise PermissionError(err)


def verify_public_narrative(workspace_url: str, ws_id: int) -> None:
    """Ensures that the workspace is public.

    Raises a PermissionError if the workspace is not public (i.e. user '*' has 'r' access).
    Creating a stating Narrative is only permitted on public Narratives.
    If the Narrative is public, this returns None.

    Raises a WorkspaceError if anything goes wrong with the lookup.

    :param workspace_url: str - the workspace endpoint url
    :param ws_id: int - the workspace to check
    """
    ws_client = Workspace(url=workspace_url)
    try:
        perms = ws_client.get_permissions({"id": ws_id})
    except ServerError as err:
        raise WorkspaceError(err, ws_id) from err
    if perms.get("*", "n") not in ["r", "w", "a"]:
        err = f"Workspace {ws_id} must be publicly readable to make a Static Narrative"
        logging.getLogger("StaticNarrative").error(err)
        raise PermissionError(err)
