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
from ..narrative.narrative_util import read_narrative
from typing import Dict
from urllib.parse import urlparse
import nbformat
import json
import os
from StaticNarrative.narrative_ref import NarrativeRef
from .data_exporter import export_narrative_data


NARRATIVE_TEMPLATE_FILE = "narrative"


class NarrativeExporter:
    def __init__(self, exporter_cfg: Dict[str, str], user_id: str, token: str):
        self.exporter_cfg = exporter_cfg
        self.ws_client = Workspace(url=exporter_cfg["workspace-url"], token=token)
        self.token = token
        self.user_id = user_id

    def export_narrative(self, narrative_ref: NarrativeRef, output_dir: str) -> str:
        """
        Exports the Narrative to an HTML file and returns the path to that file.
        :param narrative_ref: NarrativeRef - the workspace reference to the narrative object
        :param output_dir: str - the requested output file path.
        :return: str - the absolute path to the generated static Narrative HTML file.
        """
        # 1. Get the Narrative object
        try:
            nar = read_narrative(narrative_ref, self.ws_client)
            nar['metadata']['wsid'] = narrative_ref.wsid
        except ServerError as e:
            raise WorkspaceError(e, narrative_ref.wsid, "Error while exporting Narrative")

        # 2. Convert to a notebook object
        kb_notebook = nbformat.reads(json.dumps(nar), as_version=4)

        # 3. Export the Narrative workspace data to a sidecar JSON file.
        data_file_path = export_narrative_data(
            narrative_ref.wsid,
            output_dir,
            self.exporter_cfg['srv-wiz-url'],
            self.token
        )

        # 4. Export the Narrative to an HTML file
        html_exporter = self._build_exporter(data_file_path)
        (body, resources) = html_exporter.from_notebook_node(kb_notebook)

        # copy some assets
        # TODO: remove this, make them static, compile others, etc.
        # TODO: Maybe add to ui-assets repo?
        # ...maybe not yet.

        output_filename = "narrative.html"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w') as output_html:
            output_html.write(body)
        return output_path

    def _build_exporter(self, data_file_path: str) -> HTMLExporter:
        c = Config()
        c.HTMLExporter.preprocessors = [preprocessor.NarrativePreprocessor]

        # all the static files (css, fonts, etc.) are relative to this dir.
        base_path = os.path.dirname(os.path.abspath(__file__))
        service_endpt = self.exporter_cfg["kbase-endpoint"]

        endpt_parsed = urlparse(service_endpt)
        host = (endpt_parsed.scheme or "https") + "://" + endpt_parsed.netloc

        c.TemplateExporter.template_path = ['.', os.path.join(base_path, "static", "templates")]
        c.CSSHTMLHeaderPreprocessor.enabled = True
        c.NarrativePreprocessor.enabled = True
        c.ClearMetadataPreprocessor.enabled = False
        c.narrative_session.token = self.token
        c.narrative_session.user_id = self.user_id
        c.narrative_session.ws_url = self.exporter_cfg["workspace-url"]
        c.narrative_session.nms_url = self.exporter_cfg["nms-url"]
        c.narrative_session.nms_image_url = self.exporter_cfg["nms-image-url"]
        c.narrative_session.profile_page_url = self.exporter_cfg["profile-page-url"]
        c.narrative_session.auth_url = self.exporter_cfg["auth-url"]
        c.narrative_session.assets_base_url = self.exporter_cfg["assets-base-url"]
        c.narrative_session.service_wizard_url = self.exporter_cfg["srv-wiz-url"]

        c.narrative_session.host = host
        c.narrative_session.base_path = base_path
        c.narrative_session.data_file_path = data_file_path
        html_exporter = HTMLExporter(config=c)
        html_exporter.template_file = NARRATIVE_TEMPLATE_FILE
        return html_exporter
