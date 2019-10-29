# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from StaticNarrative.StaticNarrativeImpl import StaticNarrative
from StaticNarrative.StaticNarrativeServer import MethodContext
from StaticNarrative.authclient import KBaseAuth as _KBaseAuth



class StaticNarrativeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('StaticNarrative'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'StaticNarrative',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        # cls.wsURL = cls.cfg['workspace-url']
        # cls.wsClient = Workspace(cls.wsURL)
        cls.service_impl = StaticNarrative(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        # suffix = int(time.time() * 1000)
        # cls.wsName = "test_ContigFilter_" + str(suffix)
        # ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa

    @classmethod
    def tearDownClass(cls):
        pass
        # if hasattr(cls, 'wsName'):
        #     cls.wsClient.delete_workspace({'workspace': cls.wsName})
        #     print('Test workspace was deleted')

    def test_status(self):
        impl = self.service_impl
        status = impl.status(self.ctx)[0]
        self.assertEqual(status, {
            'state': "OK",
            'message': "",
            'version': impl.VERSION,
            'git_url': impl.GIT_URL,
            'git_commit_hash': impl.GIT_COMMIT_HASH
        })
        self.assertIsNotNone(status['version'])
        self.assertIsNotNone(status['git_url'])
        self.assertIsNotNone(status['git_commit_hash'])


    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_your_method(self):
        # Prepare test objects in workspace if needed using
        # self.getWsClient().save_objects({'workspace': self.getWsName(),
        #                                  'objects': []})
        #
        # Run your method by
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods
        pass
