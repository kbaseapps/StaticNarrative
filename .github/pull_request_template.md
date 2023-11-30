# Description of PR purpose/changes

* Please include a summary of the change and which issue is fixed.
* Please also include relevant motivation and context.
* List any dependencies that are required for this change.
* If you have changed the spec for the module, ensure that you have recompiled the app to generate updated versions of `StaticNarrativeImpl.py`, `StaticNarrativeServer.py`, and the compilation report, `compile_report.json`.

# Jira Ticket / Issue #

Related Jira ticket: https://kbase-jira.atlassian.net/browse/DATAUP-X
- [ ] Added the Jira Ticket to the title of the PR (e.g. `DATAUP-69 Adds a PR template`)

# Testing Instructions
* Details for how to test the PR:
- [ ] Tests pass locally and in GitHub Actions

# Dev Checklist:

- [ ] My code follows the guidelines at https://sites.google.com/lbl.gov/trussresources/home?authuser=0
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] (Python) I have run Black and Flake8 on changed Python code
- [ ] If appropriate, I have recompiled the app and added the updated `StaticNarrativeImpl.py`, `StaticNarrativeServer.py`, and `compile_report.json` to this PR.

# Updating Version and Release Notes (if applicable)

- [ ] [Version has been bumped](https://semver.org/) for each release
- [ ] [Release notes](/RELEASE_NOTES.md) have been updated for each release (and during the merge of feature branches)
