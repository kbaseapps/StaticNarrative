"""
This class does all the work of exporting a Narrative.

Once initialized and given a NarrativeRef, it will export that Narrative as HTML
to some output dir. This doesn't do the final uploading to the static site, just
the exporting.
"""
__author__ = "Bill Riehl <wjriehl@lbl.gov>"

import json
import os
from typing import Dict
from urllib.parse import urlparse

import nbformat
import StaticNarrative.exporter.preprocessor as preprocessor
from installed_clients.baseclient import ServerError
from installed_clients.WorkspaceClient import Workspace
from nbconvert import HTMLExporter
from StaticNarrative.narrative_ref import NarrativeRef
from traitlets.config import Config

from ..exceptions import WorkspaceError
from ..narrative.narrative_util import read_narrative
from .data_exporter import export_narrative_data

from StaticNarrative import STATIC_NARRATIVE_BASE_DIR

NARRATIVE_TEMPLATE_FILE = "narrative.tpl"


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
            nar["metadata"]["wsid"] = narrative_ref.wsid
        except ServerError as e:
            raise WorkspaceError(
                e, narrative_ref.wsid, "Error while exporting Narrative"
            )

        # 2. Convert to a notebook object
        kb_notebook = nbformat.reads(json.dumps(nar), as_version=4)

        # 3. Export the Narrative workspace data to a sidecar JSON file.
        exported_data = export_narrative_data(
            narrative_ref.wsid, output_dir, self.exporter_cfg["srv-wiz-url"], self.token
        )

        # 4. Export the Narrative to an HTML file
        html_exporter = self._build_exporter(exported_data, narrative_ref.wsid)
        (body, resources) = html_exporter.from_notebook_node(kb_notebook)

        # copy some assets
        # TODO: remove this, make them static, compile others, etc.
        # TODO: Maybe add to ui-assets repo?
        # ...maybe not yet.

        output_filename = "narrative.html"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "w") as output_html:
            output_html.write(body)
        return output_path

    def _build_exporter(self, exported_data: dict, ws_id: int) -> HTMLExporter:
        """
        This builds the HTMLExporter used to export the Notebook (i.e. Narrative) to
        HTML. Data is passed into the exporter by configuration with various specific
        keys set in the config traitlet.

        The NarrativePreprocessor is used to process cells for templating, and consumes
        the various elements in the narrative_session property of the config.

        This expects to see the set of data exported from the Narrative as part of
        its input - this gets passed along to the preprocessor, then to the template for
        export.

        :param exported_data: Dict - the exported data in the Narrative.
        """
        c = Config()
        c.HTMLExporter.preprocessors = [preprocessor.NarrativePreprocessor]

        # all the static files (css, fonts, etc.) are relative to this dir.
        base_path = os.path.dirname(os.path.abspath(__file__))
        service_endpt = self.exporter_cfg["kbase-endpoint"]

        endpt_parsed = urlparse(service_endpt)
        netloc = endpt_parsed.netloc
        # kinda hacky. dealing with it.
        if netloc.startswith("kbase.us"):
            netloc = "narrative." + netloc
        host = (endpt_parsed.scheme or "https") + "://" + netloc

        tpl_base_dir = os.path.join(STATIC_NARRATIVE_BASE_DIR, "lib", "StaticNarrative", "exporter", "static", "templates")
        c.TemplateExporter.template_paths = [
            tpl_base_dir,
            os.path.join(tpl_base_dir, "html"),
            os.path.join(tpl_base_dir, "skeleton"),
        ]
        c.CSSHTMLHeaderPreprocessor.enabled = True
        c.NarrativePreprocessor.enabled = True
        c.ClearMetadataPreprocessor.enabled = False

        c.narrative_session.token = self.token
        c.narrative_session.user_id = self.user_id
        c.narrative_session.ws_url = self.exporter_cfg["workspace-url"]
        c.narrative_session.nms_url = self.exporter_cfg["nms-url"]
        c.narrative_session.nms_image_url = self.exporter_cfg["nms-image-url"]
        c.narrative_session.profile_page_url = (
            host + self.exporter_cfg["profile-page-path"]
        )
        c.narrative_session.auth_url = self.exporter_cfg["auth-url"]
        c.narrative_session.assets_base_url = self.exporter_cfg["assets-base-url"]
        c.narrative_session.service_wizard_url = self.exporter_cfg["srv-wiz-url"]
        c.narrative_session.data_ie_url = self.exporter_cfg["data-ie-url"]
        c.narrative_session.host = host
        c.narrative_session.base_path = base_path
        c.narrative_session.data_file_path = exported_data["path"]
        c.narrative_session.narrative_data = exported_data
        c.narrative_session.assets_version = self.exporter_cfg["assets-version"]
        c.narrative_session.ws_id = ws_id

        html_exporter = HTMLExporter(config=c)
        html_exporter.template_file = NARRATIVE_TEMPLATE_FILE
        return html_exporter
