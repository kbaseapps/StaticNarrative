from unittest.mock import create_autospec

from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.exporter.processor_util import build_report_view_data


def test_Report_with_None_direct_link_index_and_truthy_html_links():
    """
    Tests the case where a report contains a direct_html_link_index key with a value of None
    and a truthy html_links entry. This caused a None vs. int comparison error in an earlier
    version of the code. See PUBLIC-1411
    """
    ws = create_autospec(Workspace, spec_set=True, instance=True)

    ws.get_objects2.return_value = {
        "data": [
            {
                "data": {
                    "direct_html_link_index": None,
                    "html_links": [{"name": "win32k.sys"}],
                }
            }
        ]
    }

    report_result = {"report_name": "I am report. Fear me", "report_ref": "1/2/3"}

    res = build_report_view_data("https://spongebobfreenoods.com/", ws, report_result)

    expected = {
        "objects": [],
        "summary": "",
        "summary_height": "500px",
        "html": {
            "height": "500px",
            "set_height": True,
            "links": [{"name": "win32k.sys"}],
            "paths": ["/api/v1/1/2/3/$/0/win32k.sys"],
            "link_idx": 0,
            "iframe_style": "max-height: 500px; height: 500px",
        },
    }

    assert res == expected

    ws.get_objects2.assert_called_once_with({"objects": [{"ref": "1/2/3"}]})
