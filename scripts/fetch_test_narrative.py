"""Fetches a Narrative's test data for use with this app service.

A handy way to run it locally, really.

How to run:
1. Be in StaticNarrative. (The root dir of this module)
2. Make sure lib/ is on the PYTHONPATH
    > export PYTHONPATH=$PYTHONPATH:$(pwd)/lib
3. Run it with:
    > mkdir <ws_id>
    > python scripts/fetch_test_narrative.py -e ci -t <token> -w <ws_id> -o ./<ws_id>
"""

import argparse
import json
import sys
from pathlib import Path

from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.exporter.objects_with_sets import ObjectsWithSets


def fetch_narrative_data(endpt: str, token: str, ws_id: int, outdir: str) -> int:
    """Fetch narrative data using the supplied parameters.

    :param endpt: KBase endpoint
    :type endpt: str
    :param token: auth token
    :type token: str
    :param ws_id: workspace ID
    :type ws_id: int
    :param outdir: where to save the output
    :type outdir: str
    :return: success code (0)
    :rtype: int
    """
    ws_client = Workspace(url=endpt + "ws", token=token)
    ws_info = ws_client.get_workspace_info({"id": ws_id})
    ws_meta = ws_info[8]

    # Narrative object
    narr_id = ws_meta["narrative"]
    narr_obj = ws_client.get_objects2({"objects": [{"ref": f"{ws_id}/{narr_id}"}]})["data"][0]
    narr_ver = narr_obj["info"][4]
    narr_outpath = Path(outdir) / f"narrative-{ws_id}.{narr_id}.{narr_ver}.json"
    with open(narr_outpath, "w") as fout:
        json.dump(narr_obj, fout, indent=4)

    # Report objects
    for cell in narr_obj["data"]["cells"]:
        if "kbase" in cell["metadata"]:
            meta = cell["metadata"]["kbase"]
            if "appCell" in meta:
                job_state = meta["appCell"].get("exec", {}).get("jobState", {})

                result = []
                if "result" in job_state:
                    result = job_state["result"]
                elif "job_output" in job_state and "result" in job_state["job_output"]:
                    result = job_state["job_output"]["result"]
                if len(result) > 0 and "report_ref" in result[0]:
                    report_data = ws_client.get_objects2(
                        {"objects": [{"ref": result[0]["report_ref"]}]}
                    )["data"][0]
                    report_info = report_data["info"]
                    ref_dots = f"{report_info[6]}.{report_info[0]}.{report_info[4]}"
                    report_path = Path(outdir) / f"report-{ref_dots}.json"
                    with report_path.open("w") as fout:
                        json.dump(report_data, fout, indent=4)

    # List objects results
    ows = ObjectsWithSets(workspace_client=ws_client, token=token)
    ws_data = ows.list_objects_with_sets(ws_id, includeMetadata=1)
    data_outpath = Path(outdir) / f"objects-{ws_id}.json"
    with data_outpath.open("w") as fout:
        json.dump(ws_data, fout, indent=4)

    return 0


def parse_args(args: list[str]) -> argparse.Namespace:
    """Parse input arguments to the script.

    :param args: arguments
    :type args: list[str]
    :raises ValueError: if there is no KBase environment set
    :raises ValueError: if there is not a valid WS admin auth token supplied
    :raises ValueError: if there is no workspace ID supplied
    :return: sanitised and checked args
    :rtype: argparse.Namespace
    """
    p = argparse.ArgumentParser(description=__doc__.strip())
    p.add_argument("-t", "--token", dest="token", default=None, help="User auth token")
    p.add_argument("-e", "--env", dest="env", default=None, help="KBase environment")
    p.add_argument("-w", "--ws", dest="ws_id", default=None, help="Workspace id with Narrative")
    p.add_argument("-o", "--outdir", dest="outdir", default=".", help="File output directory")
    parsed_args = p.parse_args(args)
    if parsed_args.env is None:
        msg = "env - the KBase environment - is required!"
        raise ValueError(msg)
    if parsed_args.token is None:
        msg = "token - a valid Workspace admin auth token - is required!"
        raise ValueError(msg)
    if parsed_args.ws_id is None:
        msg = "ws_id - a valid Workspace id - is required!"
        raise ValueError(msg)
    return parsed_args


def main(args: list[str]) -> int:
    """Run the script.

    :param args: arguments for the script
    :type args: list[str]
    :return: output code indicating success (0) or otherwise
    :rtype: int
    """
    parsed_args = parse_args(args)
    endpt = "kbase.us/services/"
    env = parsed_args.env + "."
    if env == "prod":
        env = ""
    endpt = f"https://{env}{endpt}"
    return fetch_narrative_data(
        endpt, parsed_args.token, int(parsed_args.ws_id), parsed_args.outdir
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
