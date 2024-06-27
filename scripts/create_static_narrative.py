"""Script to create a static narrative from the commandline."""

import argparse
import logging
import sys
from configparser import ConfigParser
from os import environ

from StaticNarrative.config import generate_config

from lib.installed_clients.WorkspaceClient import Workspace
from lib.StaticNarrative.creator import StaticNarrativeCreator
from lib.StaticNarrative.narrative_ref import NarrativeRef

DEPLOY = "KB_DEPLOYMENT_CONFIG"
SERVICE = "KB_SERVICE_NAME"


def get_config_file() -> str:
    """Get the path to the config file.

    :return: path to the config file
    :rtype: str
    """
    return environ.get(DEPLOY, "./test/deploy.cfg")


def get_service_name() -> str:
    """Get the service name.

    :return: service name
    :rtype: str
    """
    return environ.get(SERVICE, "StaticNarrative")


def get_config() -> None | dict[str, str]:
    """Retrieve the config from the config file.

    :return: parsed config as a dictionary
    :rtype: None | dict[str, str]
    """
    if not get_config_file():
        return None
    retconfig = {}
    config = ConfigParser()
    config.read(get_config_file())
    for name, value in config.items(get_service_name() or "StaticNarrative"):
        retconfig[name] = value
    return retconfig


class StaticNarrativeCmdLine:
    """Class for creating static narratives from the command line."""

    def __init__(self: "StaticNarrativeCmdLine", config: dict[str, str], token: str) -> None:
        """Init the class.

        :param self: this class
        :type self: StaticNarrativeCmdLine
        :param config: parsed config
        :type config: dict[str, str]
        :param token: token for access KBase APIs
        :type token: str
        """
        if not token or not config["workspace-url"]:
            msg = "workspace URL and a token required to initialise the StaticNarrativeCmdLine."
            raise RuntimeError(msg)
        self.config = config
        self.token = token

        logging.basicConfig(format="%(created)s %(levelname)s: %(message)s", level=logging.INFO)
        self.logger = logging.getLogger("StaticNarrative")
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def get_narrative_id_from_workspace(self: "StaticNarrativeCmdLine", ws_ref: str | int) -> str:
        """Retrieve the Narrative object from a workspace (if one exists).

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

        ws_client = Workspace(self.config["workspace-url"], token=self.token)
        results = ws_client.list_objects({ws_args: [ws_ref], "type": "KBaseNarrative.Narrative"})
        if results and results[0] and results[0][0]:
            return f"{results[0][6]}/{results[0][0]}/{results[0][4]}"

        # no narrative object
        msg = f"Workspace {ws_ref} did not contain a KBaseNarrative.Narrative object."
        raise ValueError(msg)

    def create_static_narrative(
        self: "StaticNarrativeCmdLine",
        ws_ref: str | int,
        user_id: str,
        skip_permissions_checks: str,
    ) -> None:
        """Create a static narrative from a Workspace reference.

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
        snc = StaticNarrativeCreator(self.config, token=self.token)

        self.logger.info("Creating Static Narrative %s", ref)

        if not skip_permissions_checks:
            snc.check_permissions(ref, user_id=user_id)

        output_path = snc.export_narrative(ref, user_id)
        self.logger.info("Static Narrative for %s created at %s", ref, output_path)


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse input arguments.

    :param args: input argument list
    :type args: list[str]
    :raises ValueError: if one or more of the parameters are missing
    :return: parsed arguments
    :rtype: argparse.Namespace
    """
    p = argparse.ArgumentParser()
    p.add_argument("-u", "--user", dest="user_id", default=None, help="User ID")
    p.add_argument("-t", "--token", dest="token", default=None, help="User auth token")
    p.add_argument("-w", "--ws", dest="ws_id", default=None, help="Workspace ID with Narrative")
    p.add_argument("-o", "--outdir", dest="outdir", default=".", help="File output directory")
    p.add_argument(
        "-x",
        "--skip-permissions-checks",
        dest="skip_permissions_checks",
        default=None,
        help="Skip the workspace permissions checks; omit the argument to ensure that permission checks are run.",
    )
    parsed_args = p.parse_args(args)
    errs = []
    if not parsed_args.token:
        errs.append("token - a valid Workspace admin auth token - is required!")
    if not parsed_args.ws_id:
        errs.append("ws_id - a valid Workspace id - is required!")
    if errs:
        err_str = "\n".join(["Could not create a static narrative:", *errs])
        raise ValueError(err_str)
    return parsed_args


def main(args: list[str]) -> None:
    """Run!

    :param args: input args as a list
    :type args: list[str]
    """
    parsed_args = parse_args(args)
    config = generate_config(get_config())
    if config is None:
        msg = f"No configuration data found. Please check {DEPLOY} env var points to a valid config file."
        raise RuntimeError(msg)
    sn = StaticNarrativeCmdLine(config, token=parsed_args.token)

    sn.create_static_narrative(
        parsed_args.ws_id, parsed_args.user_id, parsed_args.skip_permissions_checks
    )


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
