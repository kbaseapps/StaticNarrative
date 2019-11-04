"""
Narrative exporter
"""
__author__ = 'Bill Riehl <wjriehl@lbl.gov>'

from traitlets.config import Config
from nbconvert import (
    HTMLExporter
)
from installed_clients.WorkspaceClient import Workspace
from installed_clients.baseclient import ServerError
from ..exceptions import WorkspaceError
import StaticNarrative.exporter.preprocessor as preprocessor
from ..narrative.narrative_util import (
    validate_ref,
    read_narrative
)
from typing import Dict

import nbformat
import json
import os


NARRATIVE_TEMPLATE_FILE = "narrative"


class NarrativeExporter:
    def __init__(self, exporter_cfg: Dict[str, str], user_id: str, token: str):
        c = Config()
        c.HTMLExporter.preprocessors = [preprocessor.NarrativePreprocessor]

        # all the static files (css, fonts, etc.) are relative to this dir.
        base_path = os.path.dirname(os.path.abspath(__file__))

        c.TemplateExporter.template_path = ['.', os.path.join(base_path, "templates")]
        c.CSSHTMLHeaderPreprocessor.enabled = True
        c.NarrativePreprocessor.enabled = True
        c.ClearMetadataPreprocessor.enabled = False
        c.narrative_session.token = token
        c.narrative_session.user_id = user_id
        c.narrative_session.ws_url = exporter_cfg["workspace-url"]
        c.narrative_session.nms_url = exporter_cfg["nms-url"]
        c.narrative_session.nms_image_url = exporter_cfg["nms-image-url"]
        c.narrative_session.profile_page_url = exporter_cfg["profile-page-url"]
        c.narrative_session.auth_url = exporter_cfg["auth-url"]

        endpt = exporter_cfg["kbase-endpoint"]

        c.narrative_session.host = endpt
        c.narrative_session.base_path = base_path
        self.html_exporter = HTMLExporter(config=c)
        self.html_exporter.template_file = NARRATIVE_TEMPLATE_FILE
        self.ws_client = Workspace(url=exporter_cfg["workspace-url"], token=token)
        self.scratch = exporter_cfg["scratch"]

    def export_narrative(self, narrative_ref: str, output_filename: str = "index.html") -> str:
        """
        Exports the Narrative to an HTML file and returns the path to that file.
        :param narrative_ref: str - the workspace reference to the narrative object
        :param output_filename: str - the requested output file name that gets created in the
            scratch directory
        :return: str - the absolute path to the generated static Narrative HTML file.
        """
        validate_ref(narrative_ref)
        # 1. Get the Narrative object
        try:
            ws_id = narrative_ref.split("/")[0]
            nar = read_narrative(narrative_ref, self.ws_client)
            nar['metadata']['wsid'] = ws_id
        except ServerError as e:
            raise WorkspaceError(e, ws_id, "Error while exporting Narrative")

        # 2. Convert to a notebook object
        kb_notebook = nbformat.reads(json.dumps(nar), as_version=4)

        # 3. make the thing
        (body, resources) = self.html_exporter.from_notebook_node(kb_notebook)

        output_path = os.path.join(self.scratch, output_filename)
        with open(output_path, 'w') as output_html:
            output_html.write(body)

        return output_path
