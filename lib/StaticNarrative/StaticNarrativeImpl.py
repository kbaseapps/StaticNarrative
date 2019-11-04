# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
from StaticNarrative.exporter.exporter import NarrativeExporter

#END_HEADER


class StaticNarrative:
    '''
    Module Name:
    StaticNarrative

    Module Description:
    A KBase module: StaticNarrative
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/briehl/StaticNarrative"
    GIT_COMMIT_HASH = "6a39b78d77ea487805f17568d99edaa9cc820e31"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        self.workspace_url = config['workspace-url']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def create_static_narrative(self, ctx, CreateStaticNarrativeInput):
        """
        Creates a static Narrative from the given Narrative ref string.
        :param CreateStaticNarrativeInput: instance of type
           "CreateStaticNarrativeInput" (narrative_ref - the reference to the
           Narrative object to make a static version of. must include
           version! overwrite - if true, overwrite any previous version of
           the static Narrative.) -> structure: parameter "narrative_ref" of
           type "ws_ref" (a workspace object reference string (of the form
           wsid/objid/ver)), parameter "overwrite" of type "boolean" (allowed
           0 or 1)
        :returns: instance of type "CreateStaticNarrativeOutput" ->
           structure: parameter "static_narrative_url" of type "url"
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN create_static_narrative
        exporter = NarrativeExporter(self.workspace_url, ctx['user_id'], ctx['token'])
        #END create_static_narrative

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method create_static_narrative return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]

    def status(self, ctx):
        """
        Return the status of this dynamic service
        :returns: instance of type "Status" (state - a string, either OK or
           ...(TBD) message - optional, some message about the state of the
           service. version - a semantic version string. git_url - the GitHub
           URL where this service code is stored. git_commit_hash - the Git
           commit hash for the running version of this service.) ->
           structure: parameter "state" of String, parameter "message" of
           String, parameter "version" of String, parameter "git_url" of
           String, parameter "git_commit_hash" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN status
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END status

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method status return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]
