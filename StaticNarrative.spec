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
