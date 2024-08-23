"""Generate the deployment config file."""

import os
import os.path
import sys
from configparser import ConfigParser

from jinja2 import Template

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(  # noqa: T201
            "Usage:\nprepare_deploy_config.py <deploy_cfg_template_file> <file_with_properties>\nor:"
        )
        print(  # noqa: T201
            "KBASE_ENDPOINT=https://kbase.endpoint.url prepare_deploy_config.py <deploy_cfg_template_file>"
        )
        print(  # noqa: T201
            "Properties from <file_with_properties> or the KBASE_ENDPOINT env var will be applied to <deploy_cfg_template_file>"
        )
        print("template which will be overwritten with .orig copy saved in the same folder first.")  # noqa: T201
        sys.exit(1)

    with open(sys.argv[1]) as file:
        text = file.read()
    t = Template(text)
    config = ConfigParser()

    if os.path.isfile(sys.argv[2]):
        config.read(sys.argv[2])
    elif "KBASE_ENDPOINT" in os.environ:
        kbase_endpoint = os.environ.get("KBASE_ENDPOINT")
        props = f"[global]\nkbase_endpoint = {kbase_endpoint}\n"
        for key in os.environ:
            if key.startswith("KBASE_SECURE_CONFIG_PARAM_"):
                param_name = key[len("KBASE_SECURE_CONFIG_PARAM_") :]
                props += f"{param_name} = {os.environ.get(key)}\n"
        config.read_string(props)
    else:
        raise ValueError("Neither " + sys.argv[2] + " file nor KBASE_ENDPOINT env-variable found")

    props = dict(config.items("global"))
    output = t.render(props)
    with open(sys.argv[1] + ".orig", "w") as f:
        f.write(text)
    with open(sys.argv[1], "w") as f:
        f.write(output)
