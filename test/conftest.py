"""Test configuration."""

import os
from collections.abc import Generator
from test import TEST_BASE_DIR
from typing import Any

import pytest
from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.config import generate_config
from StaticNarrative.StaticNarrativeImpl import StaticNarrative

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

    yield generate_config(get_config())

    if deploy_config:
        os.environ[DEPLOY_CONFIG] = deploy_config
    else:
        del os.environ[DEPLOY_CONFIG]


@pytest.fixture(scope="session")
def token() -> str:
    """Retrieve an auth token for the CI server from the environment."""
    return os.environ.get("KBASE_CI_TOKEN", "some_token_string")


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
