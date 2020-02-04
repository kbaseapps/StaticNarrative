# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
from StaticNarrative.exporter.exporter import NarrativeExporter
from StaticNarrative.uploader.uploader import upload_static_narrative
from StaticNarrative.narrative_ref import NarrativeRef
from StaticNarrative.narrative.narrative_util import (
    save_narrative_url,
    get_static_info,
    verify_admin_privilege,
    verify_public_narrative
)

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
    GIT_COMMIT_HASH = "c773a0c8e98a683de627d335abe48d4b6f7d8eed"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        self.logger = logging.getLogger("StaticNarrative")
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.config = config
        #END_CONSTRUCTOR
        pass


    def create_static_narrative(self, ctx, params):
        """
        Creates a static Narrative from the given Narrative ref string.
        :param params: instance of type "CreateStaticNarrativeInput"
           (narrative_ref - the reference to the Narrative object to make a
           static version of. must include version! overwrite - if true,
           overwrite any previous version of the static Narrative.) ->
           structure: parameter "narrative_ref" of type "ws_ref" (a workspace
           object reference string (of the form wsid/objid/ver)), parameter
           "overwrite" of type "boolean" (allowed 0 or 1)
        :returns: instance of type "CreateStaticNarrativeOutput" ->
           structure: parameter "static_narrative_url" of type "url"
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN create_static_narrative

        # init - get NarrativeRef and Exporter set up
        ref = NarrativeRef.parse(params["narrative_ref"])
        ws_url = self.config["workspace-url"]
        self.logger.info(f"Creating Static Narrative {ref}")
        verify_admin_privilege(ws_url, ctx["user_id"], ctx["token"], ref.wsid)
        verify_public_narrative(ws_url, ref.wsid)
        exporter = NarrativeExporter(self.config, ctx["user_id"], ctx["token"])

        # set up output directories
        try:
            output_dir = os.path.join(
                self.config["scratch"], str(ref.wsid), str(ref.objid), str(ref.ver)
            )
            os.makedirs(output_dir, exist_ok=True)
        except IOError as e:
            self.logger.error("Error while creating Static Narrative directory", e)
            raise

        # export the narrative to a file
        try:
            output_path = exporter.export_narrative(ref, output_dir)
        except Exception as e:
            self.logger.error("Error while exporting Narrative", e)
            raise

        # upload it and save it to the Workspace metadata before returning the url path
        static_url = upload_static_narrative(ref, output_path, self.config["static-file-root"])
        save_narrative_url(self.config["workspace-url"], ctx["token"], ref, static_url)
        output = {
            "static_narrative_url": static_url
        }
        self.logger.info(f"Finished creating Static Narrative {ref}")
        #END create_static_narrative

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method create_static_narrative return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def get_static_narrative_info(self, ctx, params):
        """
        :param params: instance of type "GetStaticNarrativeInfo" ->
           structure: parameter "ws_id" of type "ws_id" (a workspace id)
        :returns: instance of type "StaticNarrativeInfo" (ws_id - the
           workspace id narrative_id - the id of the narrative object made
           static narrative_version - the version of the narrative object
           saved url - the url of the static narrative (just the path, the
           Narrative front end should provide the host) narr_saved - ms since
           epoch of when the narrative that was made static was saved.
           static_saved - ms since epoch of when the static narrative was
           saved) -> structure: parameter "ws_id" of type "ws_id" (a
           workspace id), parameter "narrative_id" of Long, parameter
           "narrative_version" of Long, parameter "url" of type "url",
           parameter "narr_saved" of Long, parameter "static_saved" of Long
        """
        # ctx is the context object
        # return variables are: info
        #BEGIN get_static_narrative_info
        info = get_static_info(self.config["workspace-url"], ctx["token"], params.get("ws_id"))
        #END get_static_narrative_info

        # At some point might do deeper type checking...
        if not isinstance(info, dict):
            raise ValueError('Method get_static_narrative_info return value ' +
                             'info is not type dict as required.')
        # return the results
        return [info]

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
