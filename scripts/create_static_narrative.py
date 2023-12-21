"""Script to create a static narrative from the commandline."""
import argparse
import logging
import sys
from configparser import ConfigParser
from os import environ
from typing import Any

from lib.installed_clients.WorkspaceClient import Workspace
from lib.StaticNarrative.creator import StaticNarrativeCreator
from lib.StaticNarrative.narrative_ref import NarrativeRef

DEPLOY = "KB_DEPLOYMENT_CONFIG"
SERVICE = "KB_SERVICE_NAME"
AUTH = "auth-service-url"


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
    for nameval in config.items(get_service_name() or "StaticNarrative"):
        retconfig[nameval[0]] = nameval[1]
    return retconfig


config = get_config()


class StaticNarrativeCmdLine:
    """Class for creating static narratives from the command line."""

    def __init__(self: "StaticNarrativeCmdLine", config: dict[str, str]) -> None:
        """Init the class.

        :param self: this class
        :type self: StaticNarrativeCmdLine
        :param config: parsed config
        :type config: dict[str, str]
        """
        logging.basicConfig(
            format="%(created)s %(levelname)s: %(message)s", level=logging.INFO
        )
        self.logger = logging.getLogger("StaticNarrative")
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.config = config

    def get_narrative_id_from_workspace(
        self: "StaticNarrativeCmdLine", ws_ref: str | int, token: str
    ) -> str:
        """Retrieve the Narrative object from a workspace (if one exists).

        :param self: this class
        :type self: StaticNarrativeCmdLine
        :param ws_ref: workspace reference (ID or name)
        :type ws_ref: str | int
        :param token: user token
        :type token: str
        :raises ValueError: if no Narrative object is found
        :return: KBaseNarrative.Narrative object UPA
        :rtype: str
        """
        ws_args = "workspaces"
        if str(ws_ref).isdigit():
            ws_args = "ids"

        ws_client = Workspace(self.config["workspace-url"], token=token)
        results = ws_client.list_objects(
            {ws_args: [ws_ref], "type": "KBaseNarrative.Narrative"}
        )
        if results[0] and results[0][0]:
            return f"{results[0][6]}/{results[0][0]}/{results[0][4]}"

        # no narrative object
        msg = f"Workspace {ws_ref} did not contain a KBaseNarrative.Narrative object."
        raise ValueError(msg)

    def create_static_narrative(
        self: "StaticNarrativeCmdLine",
        ws_ref: str | int,
        user_id: str,
        token: str,
        skip_permissions_checks: str,
    ) -> None:
        """Create a static narrative from a Workspace reference.

        :param ws_ref: workspace reference; may be the narrative UPA or a workspace ID
        :type ws_ref: str
        :param user_id: valid KBase user ID
        :type user_id: str
        :param token: KBase token, valid for whichever server the workspace is on
        :type token: str
        :param skip_permissions_checks: whether the permission checks should be run
        :type skip_permissions_checks: str
        """
        # this is a workspace reference
        if ws_ref.count("/") == 0:
            narrative_ref = self.get_narrative_id_from_workspace(ws_ref, token)
        else:
            narrative_ref = ws_ref

        ref = NarrativeRef.parse(narrative_ref)
        snc = StaticNarrativeCreator(self.config)

        log_msg = f"Creating Static Narrative {ref}"
        self.logger.info(log_msg)

        if not skip_permissions_checks:
            snc.check_permissions(ref, user_id=user_id, token=token)

        output_path = snc.export_narrative(ref, user_id, token)
        log_msg = f"Static Narrative for {ref} created at {output_path}"
        self.logger.info(log_msg)


def parse_args(args: list[str]) -> dict[str, Any]:
    """Parse input arguments.

    :param args: input argument list
    :type args: list[str]
    :raises ValueError: if one or more of the parameters are missing
    :return: parsed arguments
    :rtype: dict[str, str]
    """
    p = argparse.ArgumentParser()
    p.add_argument("-u", "--user", dest="user_id", default=None, help="User ID")
    p.add_argument("-t", "--token", dest="token", default=None, help="User auth token")
    p.add_argument("-e", "--env", dest="env", default=None, help="KBase environment")
    p.add_argument(
        "-w", "--ws", dest="ws_id", default=None, help="Workspace ID with Narrative"
    )
    p.add_argument(
        "-o", "--outdir", dest="outdir", default=".", help="File output directory"
    )
    p.add_argument(
        "-x",
        "--skip-permissions-checks",
        dest="skip_permissions_checks",
        default=None,
        help="Skip the workspace permissions checks; omit the argument to ensure that permission checks are run.",
    )
    args = p.parse_args(args)
    errs = []
    if not args.env:
        errs.append("env - the KBase environment - is required!")
    if not args.token:
        errs.append("token - a valid Workspace admin auth token - is required!")
    if not args.ws_id:
        errs.append("ws_id - a valid Workspace id - is required!")
    if errs:
        err_str = "\n".join(["Could not create a static narrative:", *errs])
        raise ValueError(err_str)
    return args


def main(args: list[str]) -> None:
    """Run!

    :param args: input args as a list
    :type args: list[str]
    """
    args = parse_args(args)
    endpt = "kbase.us/services/"
    env = args.env + "."
    if env == "prod.":
        env = ""
    endpt = f"https://{env}{endpt}"
    sn = StaticNarrativeCmdLine(config)

    sn.create_static_narrative(
        args.ws_id, args.user_id, args.token, args.skip_permissions_checks
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
