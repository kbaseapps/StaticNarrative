# StaticNarrative release notes
=========================================

0.0.14
------
* Fixed a bug that caused a None comparison error when processing a specific configuration of a
  KBaseReport (PUBLIC-1411).

0.0.13
------
* Fixed author url links.
* Add a list_static_narratives function - returns a dictionary mapping from each Static Narrative
  id to all versions available.

0.0.12
------
* Fixed duplicate text in template (metadata description).

0.0.11
------
* Include host in call to initialize Javascript on the page.

0.0.10
------
* Handle UI links in production better (kbase.us -> narrative.kbase.us)

0.0.9
-----
* Added support for direct html reports.
* Added links out to reports in a separate window.

0.0.8
-----
* Fixed error when trying to parse a data cell that doesn't have a ref key.
* Added support for "upas" key in data cell (handle copy-of-a-copy issues).

0.0.7
-----
* Fixed issue with errors that aren't being propagated properly.

0.0.6
-----
* Added Google Analytics tag to generated Static Narratives.
* Added HTML meta tags with keywords (apps and data types) and description
* Removed unused script codes from the templates.
* Removed notes about how to upgrade running containers in Rancher, since we don't need to anymore!

0.0.5
-----
* Added tabs to header of Static Narrative to flip between the main Narrative, Data, and Citations.
* Changed app cell headers to better handle runtime and final app state.
* Changed UPAs to object names in app cell configs (when they're UPAs and not names).

0.0.4
-----
* Fixed bug where non-public Narratives, or non-admin users could create Static Narratives.
* Added popup overlay with list of data in the Narrative.
* Minor Narrative cell support tweaks.

0.0.3
-----
* Add support for KBase icons font pack.

0.0.2
-----
* Added status function. Returns the status of the service, including running version and hash string for the deployed Git commit.
* Added get_static_narrative_info function. Given a workspace id, return information about the static narrative created from it, if there is any.

0.0.1
-----
* Added create_static_narrative function. Takes in a full Narrative reference (including version) and creates a static version of it, hosted on a KBase server.

0.0.0
-----
* Module created by kb-sdk init
