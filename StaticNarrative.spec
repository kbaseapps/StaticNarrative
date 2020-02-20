/*
A KBase module: StaticNarrative
*/

module StaticNarrative {
    /* allowed 0 or 1 */
    typedef int boolean;

    /* a workspace id */
    typedef int ws_id;

    /* a workspace object reference string (of the form wsid/objid/ver) */
    typedef string ws_ref;

    typedef string url;

    /*
        narrative_ref - the reference to the Narrative object to make a static version of.
                        must include version!
        overwrite - if true, overwrite any previous version of the static Narrative.
    */
    typedef structure {
        ws_ref narrative_ref;
        boolean overwrite;
    } CreateStaticNarrativeInput;

    typedef structure {
        url static_narrative_url;
    } CreateStaticNarrativeOutput;

    /*
        Creates a static Narrative from the given Narrative ref string.
    */
    funcdef create_static_narrative(CreateStaticNarrativeInput params) returns (CreateStaticNarrativeOutput output) authentication required;

    typedef structure {
        ws_id ws_id;
    } GetStaticNarrativeInfo;

    /*
        ws_id - the workspace id
        narrative_id - the id of the narrative object made static
        narrative_version - the version of the narrative object saved
        url - the url of the static narrative (just the path, the Narrative front end should provide the host)
        narr_saved - ms since epoch of when the narrative that was made static was saved.
        static_saved - ms since epoch of when the static narrative was saved
    */
    typedef structure {
        ws_id ws_id;
        int narrative_id;
        int narrative_version;
        url url;
        int narr_saved;
        int static_saved;
    } StaticNarrativeInfo;

    /*
        Returns info about a created static narrative, given the workspace id.
        If no static narrative has been created, returns an empty structure.
    */
    funcdef get_static_narrative_info(GetStaticNarrativeInfo params) returns (StaticNarrativeInfo info) authentication required;



    typedef structure {
        int count;
        mapping<ws_id, StaticNarrativeInfo> narratives;
    } AllStaticNarratives;

    funcdef list_static_narratives() returns (AllStaticNarratives narratives);

    /*
        state - a string, either OK or ...(TBD)
        message - optional, some message about the state of the service.
        version - a semantic version string.
        git_url - the GitHub URL where this service code is stored.
        git_commit_hash - the Git commit hash for the running version of this service.
    */
    typedef structure {
        string state;
        string message;
        string version;
        string git_url;
        string git_commit_hash;
    } Status;
    /*
        Return the status of this dynamic service
    */
    funcdef status() returns (Status);
};
