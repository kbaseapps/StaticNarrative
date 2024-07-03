"""This class does all the work of exporting a Narrative.

Once initialized and given a NarrativeRef, it will export that Narrative as HTML
to some output dir. This doesn't do the final uploading to the static site, just
the exporting.
"""

__author__ = "Bill Riehl <wjriehl@lbl.gov>"

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import nbformat
from installed_clients.baseclient import ServerError
from installed_clients.WorkspaceClient import Workspace
from nbconvert import HTMLExporter
from traitlets.config import Config

from StaticNarrative import STATIC_NARRATIVE_BASE_DIR
from StaticNarrative.exceptions import WorkspaceError
from StaticNarrative.exporter import preprocessor
from StaticNarrative.exporter.data_exporter import export_narrative_data
from StaticNarrative.exporter.dynamic_service_client import DynamicServiceClient
from StaticNarrative.narrative.narrative_util import read_narrative
from StaticNarrative.narrative_ref import NarrativeRef

NARRATIVE_TEMPLATE_FILE = "narrative.tpl"
OUTPUT_HTML_FILE = "narrative.html"


class NarrativeExporter:
    """Class for exporting Static Narratives."""

    def __init__(
        self: "NarrativeExporter",
        config: dict[str, str],  # config object
        user_id: str,
        token: str,
        use_set_api: int = 1,
        debug: bool = False,
    ) -> None:
        """Initialise the Narrative Exporter."""
        self.config = config
        self.ws_client = Workspace(url=config["workspace_url"], token=token)
        self.token = token
        self.user_id = user_id
        self.debug = debug
        if use_set_api:
            self.set_api_client = DynamicServiceClient(
                self.config["srv_wiz_url"], "release", "SetAPI", self.token
            )
        else:
            self.set_api_client = None

    def export_narrative(
        self: "NarrativeExporter",
        narrative_ref: NarrativeRef,
        output_dir: str,
    ) -> str:
        """Exports the Narrative to an HTML file and returns the path to that file.

        :param narrative_ref: NarrativeRef - the workspace reference to the narrative object
        :param output_dir: str - the requested output file path.
        :return: str - the absolute path to the generated static Narrative HTML file.
        """
        # 1. Get the Narrative object
        try:
            nar = read_narrative(self.ws_client, narrative_ref)
            nar["metadata"]["wsid"] = narrative_ref.wsid
        except ServerError as e:
            raise WorkspaceError(e, narrative_ref.wsid, "Error while exporting Narrative") from e

        # 2. Convert to a notebook object
        kb_notebook = nbformat.reads(json.dumps(nar), as_version=4)

        # 3. Export the Narrative workspace data to a sidecar JSON file.
        exported_data = export_narrative_data(
            self.ws_client,
            narrative_ref.wsid,
            self.token,
            output_dir,
            set_api_client=self.set_api_client,
            debug=self.debug,
        )

        # 4. Generate the data for the HTML file
        html_exporter = self._build_exporter(exported_data, narrative_ref)

        (body, resources) = html_exporter.from_notebook_node(kb_notebook)

        # copy some assets
        # TODO: remove this, make them static, compile others, etc.
        # TODO: Maybe add to ui-assets repo?
        # ...maybe not yet.

        output_path = Path(output_dir) / OUTPUT_HTML_FILE
        with output_path.open("w") as output_html:
            output_html.write(body)
        return str(output_path)

    def _build_exporter(
        self: "NarrativeExporter", exported_data: dict[str, Any], narrative_ref: NarrativeRef
    ) -> HTMLExporter:
        """Generate the magnificent HTMLExporter that will fulfil all your dreams.

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
        base_path = Path(__file__).resolve().parent
        service_endpt = self.config["kbase_endpoint"]

        endpt_parsed = urlparse(service_endpt)
        netloc = endpt_parsed.netloc
        # kinda hacky. dealing with it.
        if netloc.startswith("kbase.us"):
            netloc = "narrative." + netloc
        host = (endpt_parsed.scheme or "https") + "://" + netloc

        tpl_base_dir = (
            STATIC_NARRATIVE_BASE_DIR
            / "lib"
            / "StaticNarrative"
            / "exporter"
            / "static"
            / "templates"
        )
        c.TemplateExporter.template_paths = [
            str(tpl_base_dir),
            str(tpl_base_dir / "html"),
            str(tpl_base_dir / "skeleton"),
        ]

        c.CSSHTMLHeaderPreprocessor.enabled = True
        c.NarrativePreprocessor.enabled = True
        c.ClearMetadataPreprocessor.enabled = False

        c.narrative_session.assets_base_url = self.config["assets_base_url"]
        c.narrative_session.assets_version = self.config["assets_version"]
        c.narrative_session.auth_url = self.config["auth_url"]
        c.narrative_session.base_path = base_path
        c.narrative_session.data_file_path = exported_data["path"]
        c.narrative_session.host = host
        c.narrative_session.indexed_data = exported_data["indexed_data"]
        c.narrative_session.data_types = exported_data["types"]
        c.narrative_session.narrative_ref = narrative_ref
        c.narrative_session.nms_image_url = self.config["nms_image_url"]
        c.narrative_session.nms_url = self.config["nms_url"]
        c.narrative_session.profile_page_path = host + self.config["profile_page_path"]
        c.narrative_session.service_wizard_url = self.config["srv_wiz_url"]
        c.narrative_session.token = self.token
        c.narrative_session.user_id = self.user_id
        c.narrative_session.ws_client = self.ws_client

        html_exporter = HTMLExporter(config=c)
        html_exporter.template_file = NARRATIVE_TEMPLATE_FILE
        html_exporter.environment.add_extension("jinja2.ext.debug")
        return html_exporter
