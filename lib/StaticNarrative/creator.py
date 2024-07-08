"""Class for creating static narratives."""

import logging
from pathlib import Path
from typing import Any

from installed_clients.WorkspaceClient import Workspace

from StaticNarrative.constants import NARRATIVE_TYPE
from StaticNarrative.exporter.exporter import NarrativeExporter
from StaticNarrative.narrative.narrative_util import (
    save_narrative_url,
    verify_admin_privilege,
    verify_public_narrative,
)
from StaticNarrative.narrative_ref import NarrativeRef
from StaticNarrative.uploader.uploader import upload_static_narrative


class StaticNarrativeCreator:
    """Class for creating static narratives."""

    def __init__(self: "StaticNarrativeCreator", config: dict[str, Any], token: str) -> None:
        """Init the class.

        :param self: this class
        :type self: StaticNarrativeCreator
        :param config: configuration
        :type config: dict[str, Any]
        :param token: token for accessing KBase APIs
        :type token: str
        :return: nothing
        :rtype: None
        """
        if not token or not config or "workspace_url" not in config:
            msg = "Workspace URL and a token required to initialise the StaticNarrativeCreator."
            raise RuntimeError(msg)

        self.config = config
        self.token = token
        self.ws_client = Workspace(self.config["workspace_url"], token=token)

        logging.basicConfig(format="%(created)s %(levelname)s: %(message)s", level=logging.INFO)
        self.logger = logging.getLogger("StaticNarrative")
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def create_static_narrative(
        self: "StaticNarrativeCreator", params: dict[str, str]
    ) -> dict[str, str]:
        """Create a static narrative from a narrative reference.

        :param params: query params, including "narrative_ref" key
        :type params: dict[str, str]
        :return: dictionary containing the resulting static narrative URL
        :rtype: dict[str, str]
        """
        ref = NarrativeRef.parse(params["narrative_ref"])
        self.logger.info("Creating Static Narrative %s", ref)

        user_id = params["user_id"]
        self.check_permissions(ref, user_id=user_id)
        output_path = self.export_narrative(ref, user_id=user_id)
        # get the output directory for the upload_and_save command
        output_dir = output_path.parent
        static_url = self.upload_and_save(ref, output_dir)

        return {"static_narrative_url": static_url}

    def check_permissions(self: "StaticNarrativeCreator", ref: NarrativeRef, user_id: str) -> None:
        """Ensure the narrative and user have appropriate permissions for SN creation.

        :param ref: reference for the narrative
        :type ref: NarrativeRef
        :param user_id: user ID
        :type user_id: str
        """
        verify_admin_privilege(self.ws_client, user_id, ref.wsid)
        verify_public_narrative(self.ws_client, ref.wsid)

    def export_narrative(self: "StaticNarrativeCreator", ref: NarrativeRef, user_id: str) -> Path:
        """Create an output directory and export the SN to a file.

        :param ref: reference for the narrative
        :type ref: NarrativeRef
        :param user_id: user ID
        :type user_id: str
        :return: path to the SN created by the exporter
        :rtype: Path
        """
        exporter = NarrativeExporter(self.config, user_id, self.token)

        # set up output directories
        try:
            output_dir = (
                Path(self.config["scratch"]) / str(ref.wsid) / str(ref.objid) / str(ref.ver)
            )
            output_dir.mkdir(exist_ok=True, parents=True)
        except OSError as e:
            self.logger.exception("Error while creating Static Narrative directory")
            msg = "Could not create static narrative directory"
            raise RuntimeError(msg) from e

        # export the narrative to a file
        try:
            output_path = exporter.export_narrative(ref, output_dir)
        except Exception:
            self.logger.exception("Error while exporting Narrative")
            raise

        return output_path

    def upload_and_save(
        self: "StaticNarrativeCreator", ref: NarrativeRef, output_path: Path
    ) -> str:
        """Upload the static narrative and save the URL to the ws metadata.

        :param ref: reference for the narrative
        :type ref: NarrativeRef
        :param output_path: path to the saved output
        :type output_path: Path
        :return: URL for the static narrative
        :rtype: str
        """
        # upload it and save it to the Workspace metadata before returning the url path
        static_url = upload_static_narrative(ref, output_path, self.config["static_file_root"])
        save_narrative_url(self.ws_client, ref, static_url)
        self.logger.info("Finished creating Static Narrative %s", ref)
        return static_url

    def get_narrative_id_from_workspace(self: "StaticNarrativeCreator", ws_ref: str | int) -> str:
        """Retrieve the Narrative object from a workspace (if one exists).

        This function is used when creating a Static Narrative locally using a workspace ID as input.

        :param self: this class
        :type self: StaticNarrativeCmdLine
        :param ws_ref: workspace reference (ID or name)
        :type ws_ref: str | int
        :raises ValueError: if no Narrative object is found
        :return: KBaseNarrative.Narrative object UPA
        :rtype: str
        """
        ws_args = "workspaces"
        if str(ws_ref).isdigit():
            ws_args = "ids"

        results = self.ws_client.list_objects({ws_args: [ws_ref], "type": NARRATIVE_TYPE})
        if results and results[0] and results[0][0]:
            return f"{results[0][6]}/{results[0][0]}/{results[0][4]}"

        # no narrative object
        msg = f"Workspace {ws_ref} did not contain a {NARRATIVE_TYPE} object."
        raise ValueError(msg)

    def create_local_static_narrative(
        self: "StaticNarrativeCreator",
        ws_ref: str | int,
        user_id: str,
        skip_permissions_checks: str,
    ) -> None:
        """Create a static narrative from a Workspace reference.

        This function is used when creating a Static Narrative locally using a workspace ID as input.

        :param ws_ref: workspace reference; may be the narrative UPA or a workspace ID
        :type ws_ref: str
        :param user_id: valid KBase user ID
        :type user_id: str
        :param skip_permissions_checks: whether the permission checks should be run
        :type skip_permissions_checks: str
        """
        # this is a workspace reference
        ws_ref = str(ws_ref)
        narrative_ref = ws_ref
        if ws_ref.count("/") == 0:
            narrative_ref = self.get_narrative_id_from_workspace(ws_ref)

        ref = NarrativeRef.parse(narrative_ref)

        self.logger.info("Creating Static Narrative %s", ref)

        if not skip_permissions_checks:
            self.check_permissions(ref, user_id=user_id)

        output_path = self.export_narrative(ref, user_id)
        self.logger.info("Static Narrative for %s created at %s", ref, str(output_path))
