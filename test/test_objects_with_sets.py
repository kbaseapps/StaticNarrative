"""Tests of the ObjectsWithSets class."""

from typing import Any

import pytest
from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.exporter.dynamic_service_client import DynamicServiceClient
from StaticNarrative.exporter.objects_with_sets import ObjectsWithSets


@pytest.fixture()
def set_api_client(config: dict[str, Any], token: str) -> DynamicServiceClient:
    """Get a client for the SetAPI."""
    return DynamicServiceClient(config["srv-wiz-url"], "release", "SetAPI", token)


@pytest.fixture()
def ows(ws_client: Workspace, set_api_client: DynamicServiceClient, token: str) -> ObjectsWithSets:
    """Get an instance of ObjectsWithSets."""
    return ObjectsWithSets(set_api_client=set_api_client, workspace_client=ws_client, token=token)


def test_set_api_client_local_vs_set_api_remote(ows: ObjectsWithSets) -> None:
    """This is not really a genuine test -- it just ensures that the local vs remote calls return the same result."""
    test_workspaces = [67395, 69666]
    results = {}
    for ws in test_workspaces:
        results[ws] = ows.list_objects_with_sets(ws, include_metadata=1)

    delattr(ows, "set_api_client")
    for ws in test_workspaces:
        assert ows.list_objects_with_sets(ws, include_metadata=1) == results[ws]
