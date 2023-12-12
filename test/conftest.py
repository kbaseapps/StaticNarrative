"""Test configuration."""
import os
from configparser import ConfigParser
from test import TEST_BASE_DIR
from typing import Any

import pytest
from StaticNarrative.StaticNarrativeImpl import StaticNarrative
from StaticNarrative.StaticNarrativeServer import MethodContext

CONFIG_FILE = os.environ.get(
    "KB_DEPLOYMENT_CONFIG", os.path.join(TEST_BASE_DIR, "./deploy.cfg")
)


@pytest.fixture(scope="session")
def config() -> dict[str, str]:
    """Parses the configuration file and retrieves the values under the SetAPI header.

    :return: dictionary of key-value pairs
    :rtype: dict[str, Any]
    """
    print(f"Retrieving config from {CONFIG_FILE}")
    cfg_dict = {}
    config_parser = ConfigParser()
    config_parser.read(CONFIG_FILE)
    for nameval in config_parser.items("StaticNarrative"):
        cfg_dict[nameval[0]] = nameval[1]

    return cfg_dict


@pytest.fixture(scope="session")
def context() -> dict[str, Any]:
    """KBase context."""
    context = MethodContext(None)
    context.update(
        {
            "token": "some_token",
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
