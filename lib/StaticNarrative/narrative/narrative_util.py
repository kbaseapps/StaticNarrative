from installed_clients.WorkspaceClient import Workspace
from installed_clients.baseclient import ServerError
from ..exceptions import WorkspaceError
from typing import Dict
# from .updater import update_narrative
from StaticNarrative.narrative_ref import NarrativeRef

NARRATIVE_TYPE = "KBaseNarrative.Narrative"


def read_narrative(ref: NarrativeRef, ws_client: Workspace) -> Dict:
    """
    Fetches a Narrative and its object info from the Workspace
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
        nar_data = ws_client.get_objects2({'objects': [{'ref': str(ref)}]})
        nar = nar_data['data'][0]
        _validate_nar_type(nar['info'][2], ref)
        # nar['data'] = update_narrative(nar['data'])
        return nar['data']
    except ServerError as err:
        raise WorkspaceError(err, ref.wsid)


def _validate_nar_type(t: str, ref: str):
    if not t.startswith(NARRATIVE_TYPE):
        err = "Expected a Narrative object"
        if ref is not None:
            err += f" with reference {str(ref)}"
        err += f", got a {t}"
        raise ValueError(err)