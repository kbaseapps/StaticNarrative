# -*- coding: utf-8 -*-
# BEGIN_HEADER

from StaticNarrative.creator import StaticNarrativeCreator
from StaticNarrative.manager import StaticNarrativeManager
from StaticNarrative.narrative.narrative_util import (
    get_static_info,
)

# END_HEADER


class StaticNarrative:
    """
    Module Name:
    StaticNarrative

    Module Description:
    A KBase module: StaticNarrative
    """

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.12"
    GIT_URL = "https://github.com/briehl/StaticNarrative"
    GIT_COMMIT_HASH = "aed622bf428f5131b0c888f227495d46ef7d986d"

    # BEGIN_CLASS_HEADER
    # END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        # BEGIN_CONSTRUCTOR
        self.config = config
        # END_CONSTRUCTOR
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
        # BEGIN create_static_narrative
        snc = StaticNarrativeCreator(self.config)
        params["user_id"] = ctx["user_id"]
        params["token"] = ctx["token"]
        output = snc.create_static_narrative(params)
        # END create_static_narrative

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError(
                "Method create_static_narrative return value "
                + "output is not type dict as required."
            )
        # return the results
        return [output]

    def get_static_narrative_info(self, ctx, params):
        """
        Returns info about a created static narrative, given the workspace id.
        If no static narrative has been created, returns an empty structure.
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
        # BEGIN get_static_narrative_info
        info = get_static_info(
            self.config["workspace-url"], ctx["token"], params.get("ws_id")
        )
        # END get_static_narrative_info

        # At some point might do deeper type checking...
        if not isinstance(info, dict):
            raise ValueError(
                "Method get_static_narrative_info return value "
                + "info is not type dict as required."
            )
        # return the results
        return [info]

    def list_static_narratives(self, ctx):
        """
        :returns: instance of type "AllStaticNarratives" -> structure:
           parameter "count" of Long, parameter "narratives" of mapping from
           type "ws_id" (a workspace id) to type "StaticNarrativeInfo" (ws_id
           - the workspace id narrative_id - the id of the narrative object
           made static narrative_version - the version of the narrative
           object saved url - the url of the static narrative (just the path,
           the Narrative front end should provide the host) narr_saved - ms
           since epoch of when the narrative that was made static was saved.
           static_saved - ms since epoch of when the static narrative was
           saved) -> structure: parameter "ws_id" of type "ws_id" (a
           workspace id), parameter "narrative_id" of Long, parameter
           "narrative_version" of Long, parameter "url" of type "url",
           parameter "narr_saved" of Long, parameter "static_saved" of Long
        """
        # ctx is the context object
        # return variables are: narratives
        # BEGIN list_static_narratives
        manager = StaticNarrativeManager(self.config)
        narratives = manager.list_static_narratives()
        # END list_static_narratives

        # At some point might do deeper type checking...
        if not isinstance(narratives, dict):
            raise ValueError(
                "Method list_static_narratives return value "
                + "narratives is not type dict as required."
            )
        # return the results
        return [narratives]

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
        # BEGIN status
        returnVal = {
            "state": "OK",
            "message": "",
            "version": self.VERSION,
            "git_url": self.GIT_URL,
            "git_commit_hash": self.GIT_COMMIT_HASH,
        }
        # END status

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError(
                "Method status return value "
                + "returnVal is not type dict as required."
            )
        # return the results
        return [returnVal]
