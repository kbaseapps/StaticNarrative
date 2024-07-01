"""Test configuration."""

import json
import logging
import os
import tempfile
from collections.abc import Generator
from typing import Any

import pytest
import vcr
import vcr.request
from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.config import generate_config
from StaticNarrative.StaticNarrativeImpl import StaticNarrative

from test import TEST_BASE_DIR

DEPLOY_CONFIG = "KB_DEPLOYMENT_CONFIG"
TEST_CONFIG_FILE = os.path.join(TEST_BASE_DIR, "./deploy.cfg")


@pytest.fixture(scope="session")
def config() -> Generator:
    """Retrieve the config file for the tests.

    :return: dictionary of key-value pairs
    :rtype: dict[str, Any]
    """
    deploy_config = os.environ.get(DEPLOY_CONFIG)
    os.environ[DEPLOY_CONFIG] = TEST_CONFIG_FILE

    # make sure that we are using the test configuration file
    # so don't load `get_config` until after the appropriate env
    # vars are set
    from StaticNarrative.StaticNarrativeServer import get_config

    original_conf = get_config()
    assert original_conf is not None

    # use a temp directory for the scratch and static file root dirs
    with tempfile.TemporaryDirectory() as tmpdirname:
        original_conf["scratch"] = tmpdirname
        original_conf["static-file-root"] = os.path.join(
            original_conf["scratch"], "static_file_root"
        )
        os.makedirs(original_conf["static-file-root"], exist_ok=True)

        yield generate_config(original_conf)

    if deploy_config:
        os.environ[DEPLOY_CONFIG] = deploy_config
    else:
        del os.environ[DEPLOY_CONFIG]


@pytest.fixture(scope="session")
def token() -> str:
    """Retrieve an auth token for the CI server from the environment."""
    return os.environ.get(
        "KBASE_CI_TOKEN", os.environ.get("CI_KBASE_TEST_TOKEN", "some_token_string")
    )


@pytest.fixture(scope="session")
def workspace_client(config: dict[str, Any], token: str) -> Workspace:
    """Workspace client."""
    return Workspace(config["workspace-url"], token=token)


@pytest.fixture(scope="session")
def context(token: str) -> dict[str, Any]:
    """KBase context."""
    from StaticNarrative.StaticNarrativeServer import MethodContext

    context = MethodContext(None)
    context.update(
        {
            "token": token,
            "user_id": "some_user",
            "provenance": [
                {
                    "service": "StaticNarrative",
                    "method": "please_never_use_it_in_production",
                    "method_params": [],
                }
            ],
            "authenticated": 1,
        }
    )
    return context


@pytest.fixture(scope="session")
def static_narrative_service(config: dict[str, str]) -> StaticNarrative:
    """Static Narrative server object."""
    return StaticNarrative(config)


@pytest.fixture(scope="session")
def scratch_dir(config: dict[str, str]) -> str:
    """Scratch directory."""
    return config["scratch"]


@pytest.fixture(scope="session")
def workspace_url(config: dict[str, str]) -> str:
    """Workspace URL."""
    return config["workspace-url"]


# initialise logging for vcrpy
logging.basicConfig()
vcr_log = logging.getLogger("vcr")
# set to INFO or DEBUG for debugging
vcr_log.setLevel(logging.WARNING)


def body_matcher(r1: vcr.request.Request, r2: vcr.request.Request) -> None:
    """Compare the body contents of two requests to work out if they are identical or not."""
    r1_body = json.loads(r1.body.decode())
    r2_body = json.loads(r2.body.decode())
    if "id" in r1_body:
        del r1_body["id"]
    if "id" in r2_body:
        del r2_body["id"]
    assert r1_body == r2_body


MATCH_ON = ["method", "scheme", "host", "path", "body_matcher"]

vcr_conf = {
    "record_mode": vcr.record_mode.RecordMode.ONCE,
    "filter_headers": ["authorization"],
    "match_on": MATCH_ON,
}


@pytest.fixture(scope="session")
def vcr_config() -> dict[str, Any]:
    """Config for the VCR used in the tests."""
    return vcr_conf


def pytest_recording_configure(config: dict[str, Any], vcr: vcr.config.VCR) -> None:
    """Register the body_matcher with the VCR used in the tests."""
    vcr.register_matcher("body_matcher", body_matcher)
