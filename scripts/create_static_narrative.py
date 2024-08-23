"""Script to create a static narrative from the commandline.

Arguments:
-u, --user   <str>  KBase user ID
-t, --token  <str>  valid KBase token for the KBase user above
-w, --ws     <int>  numeric ID of the workspace to generate the static narrative for
-x, --skip-permissions-checks
                    if this argument is omitted, the script checks that user has admin
                    privileges for the workspace and that the workspace is readable by
                    all. This is useful for generating a static narrative for workspaces
                    that the user has access to but has not made public.


Invocation:

1. Be in StaticNarrative (the root dir of this module).

2. Make sure lib/ is on the PYTHONPATH
    > export PYTHONPATH=$PYTHONPATH:$(pwd)/lib

3. Create a 'deploy.cfg' file with the appropriate values for `kbase_endpoint`
    and `scratch`. Set the env var KB_DEPLOYMENT_CONFIG to the path to this file.
    > export KB_DEPLOYMENT_CONFIG=$(pwd)/local_deploy.cfg

4. Run it with:
    > python scripts/create_static_narrative.py -u <username> -t <token> -w <ws_id>

    If the workspace object for the narrative is 12345/6/7, the generated static
    narrative will appear in the directory

    <scratch dir from deploy.cfg> / 12345 / 6 / 7

"""

import argparse
import sys
from configparser import ConfigParser
from os import environ

from StaticNarrative.config import generate_config

from lib.StaticNarrative.creator import StaticNarrativeCreator

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
    config = ConfigParser()
    config.read(get_config_file())
    return dict(config.items(get_service_name() or "StaticNarrative"))


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

    sn = StaticNarrativeCreator(config, token=parsed_args.token)

    sn.create_local_static_narrative(
        parsed_args.ws_id, parsed_args.user_id, parsed_args.skip_permissions_checks
    )


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
