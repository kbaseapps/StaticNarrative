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
        c.TemplateExporter.template_path = ['.', self._narrative_template_path()]
        c.CSSHTMLHeaderPreprocessor.enabled = True
        c.NarrativePreprocessor.enabled = True
        c.ClearMetadataPreprocessor.enabled = False
        c.narrative_session.token = token
        c.narrative_session.user_id = user_id
        c.narrative_session.ws_url = exporter_cfg["workspace-url"]
        c.narrative_session.nms_url = exporter_cfg["nms-url"]
        c.narrative_session.nms_image_url = exporter_cfg["nms-image-url"]
        c.narrative_session.profile_page_url = exporter_cfg["profile-page-url"]
        c.narrative_session.auth_url = exporter_cfg["auth-service-url"]
        c.narrative_session.host = "https://some_host.kbase.us"
        self.html_exporter = HTMLExporter(config=c)
        self.html_exporter.template_file = NARRATIVE_TEMPLATE_FILE
        self.ws_client = Workspace(url=exporter_cfg["workspace-url"], token=token)

    def _narrative_template_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

    def export_narrative(self, narrative_ref: str, output_file: str) -> None:
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

        with open(output_file, 'w') as output_html:
            output_html.write(body)

        # 4. Upload it to its final destination (later)
