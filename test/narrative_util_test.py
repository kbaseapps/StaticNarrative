import time
import unittest
import requests
import requests_mock
from test.test_config import get_test_config
from test.mocks import (
    set_up_ok_mocks,
    mock_ws_bad
)
from installed_clients.WorkspaceClient import Workspace
from StaticNarrative.exceptions import WorkspaceError
from StaticNarrative.narrative.narrative_util import (
    read_narrative,
    _validate_narr_type,
    get_static_info,
    save_narrative_url,
    verify_admin_privilege,
    verify_public_narrative
)
from StaticNarrative.narrative_ref import NarrativeRef


class NarrativeUtilTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user_id = "some_user"
        cls.token = "some_token"
        cls.cfg = get_test_config()

    @requests_mock.Mocker()
    def test_read_narrative_ok(self, rqm):
        ref = "43666/1/18"
        ref_to_file = {ref: "data/narrative-43666.1.18.json"}
        set_up_ok_mocks(rqm, ref_to_file=ref_to_file)
        nar = read_narrative(NarrativeRef.parse("43666/1/18"),
                             Workspace(url=self.cfg["workspace-url"], token=self.token))
        # spot check that it's loaded and formatted
        self.assertIsNotNone(nar)
        self.assertIn("cells", nar)
        self.assertEqual(len(nar["cells"]), 9)

    @requests_mock.Mocker()
    def test_read_narrative_bad_client(self, rqm):
        ws_id = 908
        mock_ws_bad(rqm, "Can't fetch object")
        with self.assertRaises(WorkspaceError) as e:
            read_narrative(NarrativeRef.parse("908/1/1"),
                           Workspace(url=self.cfg["workspace-url"], token=self.token))
        self.assertIn(str(ws_id), str(e.exception))
        self.assertIn("Can't fetch object", str(e.exception))

    @requests_mock.Mocker()
    def test_read_narrative_not_narrative(self, rqm):
        ref = "43666/3/1"
        ref_to_file = {ref: "data/report-43666.3.1.json"}
        set_up_ok_mocks(rqm, ref_to_file=ref_to_file)
        with self.assertRaises(ValueError) as e:
            read_narrative(NarrativeRef.parse(ref),
                           Workspace(url=self.cfg["workspace-url"], token=self.token))
        self.assertIn(
            f"Expected a Narrative object with reference {ref}, got a KBaseReport.Report-3.0",
            str(e.exception)
        )

    def test_validate_narr_type(self):
        good_types = [
            "KBaseNarrative.Narrative-1.0",
            "KBaseNarrative.Narrative-4.0"
        ]
        bad_types = [
            "SomeObject.Name",
            "kbasenarrative.Narrative-1.0"
            "KBaseNarrative.Narrative-1.0.0"
        ]
        invalid_types = [
            5,
            str,
            {"lol": "no"},
            ["wat"],
            None
        ]
        ref = NarrativeRef.parse("1/2/3")
        for t in good_types:
            self.assertIsNone(_validate_narr_type(t, ref))
        for t in bad_types:
            with self.assertRaises(ValueError) as e:
                _validate_narr_type(t, ref)
            self.assertIn(f"Expected a Narrative object with reference {str(ref)}, got a",
                          str(e.exception))
        for t in invalid_types:
            with self.assertRaises(ValueError) as e:
                _validate_narr_type(t, ref)
            self.assertIn(f"The type string must be a string",
                          str(e.exception))

    @requests_mock.Mocker()
    def test_save_narrative_url(self, rqm):
        pass

    @requests_mock.Mocker()
    def test_save_narrative_url_bad(self, rqm):
        mock_ws_bad(rqm, "Failed to alter metadata")
        ws_id = 234
        with self.assertRaises(WorkspaceError) as e:
            save_narrative_url(self.cfg["workspace-url"], self.token,
                               NarrativeRef.parse("234/1/2"), "/234/1")
        self.assertIn("Failed to alter metadata", str(e.exception))
        self.assertIn(str(ws_id), str(e.exception))

    def test_get_static_info_bad(self):
        bad_wsids = [
            "foo",
            "onetwo",
            {"no": "way"},
            ["nope"],
            None,
            str
        ]
        for ws_id in bad_wsids:
            with self.assertRaises(ValueError) as e:
                get_static_info("someurl", "some_token", ws_id)
            self.assertIn("The parameter ws_id must be an integer, not ", str(e.exception))

    @requests_mock.Mocker()
    def test_get_static_info_ok(self, rqm):
        ws_id1 = 123
        ws_id2 = 456
        save_time = str(int(time.time()*1000))
        ws_ts = '2019-08-26T17:33:56+0000'
        ws_ts_epoch = 1566840836000
        obj_info = [
            1, 'fake_narr', 'KBaseNarrative.Narrative-4.0', ws_ts, 1, 'some_user',
            5, 'fake_ws', 'an_md5', 12345, None
        ]
        ref_to_info = {
            f"{ws_id1}/1/1": obj_info,
            f"{ws_id2}/1/1": obj_info
        }
        ws_info_map = {
            ws_id1: [
                ws_id1,
                'some_util_test_narrative',
                self.user_id,
                ws_ts,
                7,
                'a',
                'r',
                'unlocked',
                {
                    'cell_count': '1',
                    'narrative_nice_name': 'Test Exporting 1',
                    'searchtags': 'narrative',
                    'is_temporary': 'false',
                    'narrative': '1'
                }
            ],
            ws_id2: [
                ws_id2,
                'some_other_util_test_narrative',
                self.user_id,
                ws_ts,
                7,
                'a',
                'r',
                'unlocked',
                {
                    'cell_count': '1',
                    'narrative_nice_name': 'Test Exporting',
                    'searchtags': 'narrative',
                    'is_temporary': 'false',
                    'narrative': '1',
                    "static_narrative_ver": "1",
                    "static_narrative_saved": save_time,
                    "static_narrative": f"/{ws_id2}/1"
                }
            ]
        }
        set_up_ok_mocks(rqm, ref_to_info=ref_to_info, ws_info=ws_info_map[ws_id1])
        info = get_static_info(self.cfg["workspace-url"], self.token, ws_id1)
        self.assertEqual(info, {})

        set_up_ok_mocks(rqm, ref_to_info=ref_to_info, ws_info=ws_info_map[ws_id2])
        info = get_static_info(self.cfg["workspace-url"], self.token, ws_id2)
        self.assertEqual(info, {
            "ws_id": ws_id2,
            "narrative_id": 1,
            "version": 1,
            "url": f"/{ws_id2}/1",
            "static_saved": int(save_time),
            "narr_saved": ws_ts_epoch
        })

    @requests_mock.Mocker()
    def test_static_info_ws_err(self, rqm):
        mock_ws_bad(rqm, "Workspace not found")
        with self.assertRaises(WorkspaceError) as e:
            get_static_info(self.cfg["workspace-url"], self.token, 123)
        self.assertIn("123", str(e.exception))

    @requests_mock.Mocker()
    def test_verify_admin_privs_ok(self, rqm):
        ws_ids_ok = {
            123: {self.user_id: "a"},
            "1123": {self.user_id: "a"}
        }
        set_up_ok_mocks(rqm, ws_perms=ws_ids_ok)
        for ws_id in ws_ids_ok:
            self.assertIsNone(verify_admin_privilege(
                self.cfg["workspace-url"], self.user_id, self.token, ws_id
            ))

    @requests_mock.Mocker()
    def test_verify_admin_privs_fail(self, rqm):
        ws_no_privs = {
            123: {self.user_id: "n"},
            456: {self.user_id: "w"},
            789: {self.user_id: "r"},
            234: {"some_other_user": "a", "*": "r"}
        }
        set_up_ok_mocks(rqm, ws_perms=ws_no_privs)
        for ws_id in ws_no_privs:
            with self.assertRaises(PermissionError) as e:
                verify_admin_privilege(
                    self.cfg["workspace-url"], self.user_id, self.token, ws_id
                )
            self.assertIn(
                f"User {self.user_id} does not have admin rights on workspace {ws_id}",
                str(e.exception)
            )

    @requests_mock.Mocker()
    def test_verify_admin_privs_bad_client(self, rqm):
        mock_ws_bad(rqm, "Can't reach workspace")
        ws_id = 5
        with self.assertRaises(WorkspaceError) as e:
            verify_admin_privilege(self.cfg["workspace-url"], self.user_id, self.token, ws_id)
        self.assertIn("Can't reach workspace", str(e.exception))
        self.assertIn(str(ws_id), str(e.exception))

    @requests_mock.Mocker()
    def test_verify_public_narrative_ok(self, rqm):
        # all kinda stupid, but valid.
        ws_perms = {
            123: {self.user_id: "a", "*": "r"},
            456: {self.user_id: "n", "*": "w"},
            "789": {self.user_id: "r", "*": "a"}
        }
        set_up_ok_mocks(rqm, ws_perms=ws_perms)
        for ws_id in ws_perms:
            self.assertIsNone(verify_public_narrative(
                self.cfg["workspace-url"], ws_id
            ))

    @requests_mock.Mocker()
    def test_verify_public_narrative_fail(self, rqm):
        ws_no_privs = {
            123: {self.user_id: "n"},
            "456": {self.user_id: "a"},
            789: {self.user_id: "w"}
        }
        set_up_ok_mocks(rqm, ws_perms=ws_no_privs)
        for ws_id in ws_no_privs:
            with self.assertRaises(PermissionError) as e:
                verify_public_narrative(
                    self.cfg["workspace-url"], ws_id
                )
            self.assertIn(
                f"Workspace {ws_id} must be publicly readable to make a Static Narrative",
                str(e.exception)
            )

    @requests_mock.Mocker()
    def test_verify_public_privs_bad_client(self, rqm):
        mock_ws_bad(rqm, "Can't reach workspace")
        ws_id = 666
        with self.assertRaises(WorkspaceError) as e:
            verify_public_narrative(self.cfg["workspace-url"], ws_id)
        self.assertIn("Can't reach workspace", str(e.exception))
        self.assertIn(str(ws_id), str(e.exception))
