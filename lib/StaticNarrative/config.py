"""Config for the StaticNarrative app."""

import os
from typing import Any
from urllib.parse import urlparse


def generate_config(config: dict[str, Any] | None) -> None | dict[str, Any]:
    """Generate the config for the StaticNarrative, with some tweaks."""
    if not config:
        return {}

    kbase_endpoint = config.get("kbase-endpoint")
    if kbase_endpoint == "{{ kbase_endpoint }}":
        msg = "Config file has not been populated correctly"
        raise RuntimeError(msg)

    parsed_endpt = urlparse(kbase_endpoint)
    base_url = f"{parsed_endpt.scheme}://{parsed_endpt.netloc}"

    config.update(
        {
            "workspace-url": f"{kbase_endpoint}/ws",
            "srv-wiz-url": f"{kbase_endpoint}/service_wizard",
            "auth-url": f"{kbase_endpoint}/auth",
            "nms-url": f"{kbase_endpoint}/narrative_method_store/rpc",
            "nms-image-url": f"{kbase_endpoint}/narrative_method_store/",
            "assets-base-url": f"{base_url}/ui-assets",
        }
    )

    # ensure these paths are absolute, not relative
    for path in ["static-file-root", "scratch"]:
        assigned_path = config.get(path)
        if assigned_path is None:
            msg = f"Missing required config setting {path}"
            raise RuntimeError(msg)

        if not os.path.isabs(assigned_path):
            config[path] = os.path.abspath(assigned_path)

        # check that the directory exists and is writeable
        if not os.path.isdir(config[path]):
            msg = f"{path}: {config[path]} is not a directory"
            raise RuntimeError(msg)

        if path == "scratch" and not os.access(config[path], os.W_OK):
            msg = f"Cannot write to directory {config[path]}"
            raise RuntimeError(msg)

    return config
