# -*- coding: utf-8 -*-
import unittest
from test.mocks import set_up_ok_mocks
from test.test_config import get_test_config

import requests_mock
from StaticNarrative.StaticNarrativeImpl import StaticNarrative
from StaticNarrative.StaticNarrativeServer import MethodContext


class StaticNarrativeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = get_test_config()
        cls.ctx = MethodContext(None)
        cls.ctx.update(
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
        cls.service_impl = StaticNarrative(cls.cfg)
        cls.scratch = cls.cfg["scratch"]
        cls.user_id = "some_user"

    def test_status(self):
        impl = self.service_impl
        status = impl.status(self.ctx)[0]
        self.assertEqual(
            status,
            {
                "state": "OK",
                "message": "",
                "version": impl.VERSION,
                "git_url": impl.GIT_URL,
                "git_commit_hash": impl.GIT_COMMIT_HASH,
            },
        )
        self.assertIsNotNone(status["version"])
        self.assertIsNotNone(status["git_url"])
        self.assertIsNotNone(status["git_commit_hash"])

    @requests_mock.Mocker()
    def test_create_static_narrative_ok_unit(self, rqm):
        """
        Runs through the create process with a number of narratives.
        """
        ref_to_file = {}
        # 1. Add ref -> file for narratives
        narr_refs = [
            "5846/1/19",
            "25022/1/114",
            "30530/107/25",
            "40800/178/1",
            "43666/1/18",
            "43666/1/21",
            "54980/144/1",
            "47123/1/28",
        ]
        ws_to_reports = {
            "5846": [],
            "25022": [
                "25022/4",
                "25022/6",
                "25022/8",
                "25022/9",
                "25022/11",
                "25022/12",
                "25022/13",
                "25022/19",
                "25022/20",
                "25022/31",
                "25022/34",
            ],
            "30530": [
                "30462/16",
                "30462/73",
                "30462/80",
                "30462/82",
                "30462/96",
                "30462/105",
                "30462/106",
                "30530/108",
                "30530/109",
                "30530/110",
                "30530/111",
                "30530/112",
                "30530/113",
                "30530/114",
            ],
            "40800": [
                "40589/17/2",
                "40589/22/3",
                "40589/30/2",
                "40589/31",
                "40589/32",
                "40589/43",
                "40589/44",
                "40589/175",
            ],
            "43666": ["43666/3", "43666/7"],
            "47123": ["47123/4", "47123/5", "47123/6", "47123/7", "47123/8", "47123/9"],
            "54980": ["24065/141", "24065/143"],
        }
        for ref in narr_refs:
            ws_id = ref.split("/")[0]
            ref_dots = ref.replace("/", ".")
            ref_to_file[ref] = f"data/{ws_id}/narrative-{ref_dots}.json"
        for ws_id in ws_to_reports:
            for report_ref in ws_to_reports[ws_id]:
                if len(report_ref.split("/")) == 2:
                    report_ref = report_ref + "/1"
                ref_dots = report_ref.replace("/", ".")
                ref_to_file[report_ref] = f"data/{ws_id}/report-{ref_dots}.json"
        for narr_ref in narr_refs:
            ws_id = int(narr_ref.split("/")[0])
            ws_info = [
                ws_id,
                "some_narrative",
                self.user_id,
                "2019-08-26T17:33:56+0000",
                7,
                "a",
                "r",
                "unlocked",
                {
                    "cell_count": "1",
                    "narrative_nice_name": "Test Exporting",
                    "searchtags": "narrative",
                    "is_temporary": "false",
                    "narrative": "1",
                },
            ]
            ws_perms = {ws_id: {self.user_id: "a", "*": "r", "some_other_user": "w"}}
            user_map = {self.user_id: "Some User", "some_other_user": "Some Other User"}
            set_up_ok_mocks(
                rqm,
                ref_to_file=ref_to_file,
                ref_to_info={},
                ws_info=ws_info,
                ws_perms=ws_perms,
                user_map=user_map,
                ws_obj_info_file=f"data/{ws_id}/objects-{ws_id}.json",
            )
            output = self.service_impl.create_static_narrative(
                self.ctx, {"narrative_ref": narr_ref}
            )[0]
            self.assertEqual(
                output["static_narrative_url"], f"/{ws_id}/{narr_ref.split('/')[-1]}/"
            )

    def test_create_static_narrative_no_auth(self):
        """
        Test case where user isn't logged in, or just no auth token passed.
        """
        pass

    @requests_mock.Mocker()
    def test_create_static_narrative_user_not_admin(self, rqm):
        """
        Test case where user doesn't have admin rights on the workspace.
        """
        ws_id = 12345
        set_up_ok_mocks(
            rqm,
            ws_perms={ws_id: {self.user_id: "n"}},
            user_map={self.user_id: "Some User"},
        )
        with self.assertRaises(PermissionError) as e:
            self.service_impl.create_static_narrative(
                self.ctx, {"narrative_ref": f"{ws_id}/1/1"}
            )
        self.assertIn(
            f"User {self.user_id} does not have admin rights on workspace {ws_id}",
            str(e.exception),
        )

    @requests_mock.Mocker()
    def test_create_static_narrative_not_public(self, rqm):
        """
        Test case where Narative isn't public.
        """
        ws_perms = {123: {self.user_id: "a", "*": "n"}, 456: {self.user_id: "a"}}
        set_up_ok_mocks(rqm, ws_perms=ws_perms, user_map={self.user_id: "Some User"})
        for ws_id in ws_perms:
            with self.assertRaises(PermissionError) as e:
                self.service_impl.create_static_narrative(
                    self.ctx, {"narrative_ref": f"{ws_id}/1/1"}
                )
            self.assertIn(
                f"Workspace {ws_id} must be publicly readable to make a Static Narrative",
                str(e.exception),
            )

    def test_create_static_narrative_bad(self):
        """
        Test case with a badly formed Narrative object.
        """
        pass

    @requests_mock.Mocker()
    def test_get_static_info_ok(self, rqm):
        ws_id = 5
        ws_name = "fake_ws"
        ts_iso = "2019-10-24T21:51:17+0000"
        ws_meta = {
            "cell_count": "1",
            "narrative_nice_name": "Tester",
            "searchtags": "narrative",
            "is_temporary": "false",
            "narrative": "1",
            "static_narrative_ver": "1",
            "static_narrative_saved": "1573170933432",
            "static_narrative": "/5/1",
        }
        ref_to_file = {}
        ref_to_info = {
            "5/1/1": [
                1,
                "fake_narr",
                "KBaseNarrative.Narrative-4.0",
                ts_iso,
                1,
                self.user_id,
                ws_id,
                ws_name,
                "an_md5",
                12345,
                None,
            ]
        }
        ws_info = [5, ws_name, self.user_id, ts_iso, 1, "a", "r", "unlocked", ws_meta]
        set_up_ok_mocks(
            rqm, ref_to_file=ref_to_file, ref_to_info=ref_to_info, ws_info=ws_info
        )
        info = self.service_impl.get_static_narrative_info(self.ctx, {"ws_id": ws_id})[
            0
        ]
        std_info = {
            "ws_id": ws_id,
            "version": 1,
            "narrative_id": 1,
            "url": "/5/1",
            "static_saved": 1573170933432,
            "narr_saved": 1571953877000,
        }
        self.assertEqual(info, std_info)

    def test_list_static_narratives(self):
        """
        TODO: better testing. set up specific files, narratives, maybe run all the things first.
        TODO: deeper unit testing?
        """
        narrs = self.service_impl.list_static_narratives(self.ctx)[0]
        print(narrs)
