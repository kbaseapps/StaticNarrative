"""
Fetches a Narrative's test data for use with this app service.
A handy way to run it locally, really.

How to run:
1. Be in StaticNarrative. (The root dir of this module)
2. Make sure lib/ is on the PYTHONPATH
    > export PYTHONPATH=$PYTHONPATH:$(pwd)/lib
3. Run it with:
    > mkdir <ws_id>
    > python test/fetch_test_narrative.py -e ci -t <token> -w <ws_id> -o ./<ws_id>
"""
import argparse
import json
import os
import sys

from installed_clients.NarrativeServiceClient import NarrativeService
from installed_clients.WorkspaceClient import Workspace


def fetch_narrative_data(endpt: str, token: str, ws_id: int, outdir: str) -> int:
    ws_client = Workspace(url=endpt + "ws", token=token)
    ws_info = ws_client.get_workspace_info({"id": ws_id})
    ws_meta = ws_info[8]

    # Narrative object
    narr_id = ws_meta["narrative"]
    narr_obj = ws_client.get_objects2({"objects": [{"ref": f"{ws_id}/{narr_id}"}]})[
        "data"
    ][0]
    narr_ver = narr_obj["info"][4]
    narr_outpath = os.path.join(outdir, f"narrative-{ws_id}.{narr_id}.{narr_ver}.json")
    with open(narr_outpath, "w") as fout:
        json.dump(narr_obj, fout, indent=4)

    # Report objects
    for cell in narr_obj["data"]["cells"]:
        if "kbase" in cell["metadata"]:
            meta = cell["metadata"]["kbase"]
            if "appCell" in meta:
                job_state = meta["appCell"].get("exec", {}).get("jobState")
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
                    report_path = os.path.join(outdir, f"report-{ref_dots}.json")
                    with open(report_path, "w") as fout:
                        json.dump(report_data, fout, indent=4)

    # List objects results
    service = NarrativeService(url=endpt + "service_wizard", token=token)
    ws_data = service.list_objects_with_sets({"ws_id": ws_id, "includeMetadata": 1})
    data_outpath = os.path.join(outdir, f"objects-{ws_id}.json")
    with open(data_outpath, "w") as fout:
        json.dump(ws_data, fout, indent=4)

    return 0


def parse_args(args: list[str]) -> dict[str, str]:
    p = argparse.ArgumentParser(description=__doc__.strip())
    p.add_argument("-t", "--token", dest="token", default=None, help="User auth token")
    p.add_argument("-e", "--env", dest="env", default=None, help="KBase environment")
    p.add_argument(
        "-w", "--ws", dest="ws_id", default=None, help="Workspace id with Narrative"
    )
    p.add_argument(
        "-o", "--outdir", dest="outdir", default=".", help="File output directory"
    )
    args = p.parse_args(args)
    if args.env is None:
        raise ValueError("env - the KBase environment - is required!")
    if args.token is None:
        raise ValueError("token - a valid Workspace admin auth token - is required!")
    if args.ws_id is None:
        raise ValueError("ws_id - a valid Workspace id - is required!")
    return args


def main(args: list[str]) -> int:
    args = parse_args(args)
    endpt = "kbase.us/services/"
    env = args.env + "."
    if env == "prod":
        env = ""
    endpt = f"https://{env}{endpt}"
    return fetch_narrative_data(endpt, args.token, int(args.ws_id), args.outdir)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
