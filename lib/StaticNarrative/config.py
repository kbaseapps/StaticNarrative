"""Config for the StaticNarrative app."""

import os
from typing import Any
from urllib.parse import urlparse


def generate_config(config: dict[str, Any] | None) -> dict[str, Any]:
    """Generate the config for the StaticNarrative, with some tweaks."""
    if not config:
        msg = "No config information found"
        raise RuntimeError(msg)

    required_values = ["kbase_endpoint", "scratch", "static_file_root"]
    if not all(config.get(v) for v in required_values):
        missing = [v for v in required_values if not config.get(v)]
        msg = f"Missing required config values: {', '.join(missing)}"
        raise RuntimeError(msg)

    kbase_endpoint = config.get("kbase_endpoint")
    if kbase_endpoint == "{{ kbase_endpoint }}":
        msg = "Config file has not been populated correctly"
        raise RuntimeError(msg)

    parsed_endpt = urlparse(kbase_endpoint)
    base_url = f"{parsed_endpt.scheme}://{parsed_endpt.netloc}"

    config.update(
        {
            "workspace_url": f"{kbase_endpoint}/ws",
            "srv_wiz_url": f"{kbase_endpoint}/service_wizard",
            "auth_url": f"{kbase_endpoint}/auth",
            "nms_url": f"{kbase_endpoint}/narrative_method_store/rpc",
            "nms_image_url": f"{kbase_endpoint}/narrative_method_store/",
            "assets_base_url": f"{base_url}/ui-assets",
        }
    )

    # ensure these paths are absolute, not relative
    for path in ["static_file_root", "scratch"]:
        assigned_path = config.get(path)

        if not os.path.isabs(assigned_path):
            config[path] = os.path.abspath(assigned_path)

        # check that the directory exists and is writable
        if not os.path.isdir(config[path]):
            msg = f"{path}: {config[path]} is not a directory"
            raise RuntimeError(msg)

        if path == "scratch" and not os.access(config[path], os.W_OK):
            msg = f"Cannot write to directory {config[path]}"
            raise RuntimeError(msg)

    return config
