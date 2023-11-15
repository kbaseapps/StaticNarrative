import re
from typing import T

from installed_clients.baseclient import ServerError


class PermissionsError(ServerError):
    """Raised if user does not have permission to
    access the workspace.
    """

    @staticmethod
    def is_permissions_error(err: str) -> bool:
        """Try to guess if the error string is a permission-denied error
        for the narrative (i.e. the workspace the narrative is in).
        """
        pat = re.compile(
            r"(\s*users?\s*(\w+)?\s*may not \w+ workspace.*)|(\s*token validation failed)",
            re.IGNORECASE,
        )
        return pat.search(err) is not None

    def __init__(
        self: "PermissionsError",
        name: str | None = None,
        code: int | None = None,
        message: str | None = None,
        **kw: None | dict[str, T],
    ) -> None:
        ServerError.__init__(self, name, code, message, **kw)


class WorkspaceError(Exception):
    def __init__(
        self: "WorkspaceError",
        ws_server_err: ServerError,
        ws_id: str,
        message: str | None = None,
        http_code: int | None = 500,
    ) -> None:
        """
        This wraps Workspace calls regarding Narratives into exceptions that are
        easier to parse for logging, user communication, etc.

        ws_server_err should be the ServerError that comes back from a workspace
        response. This will still try to infer what happened and make it easier to get to,
        but it's best to use a ServerError.

        If there's a useful message, then that will be used to set the http_code, and
        can override the kwarg input.
        """
        self.err = ws_server_err
        self.ws_id = ws_id
        self.http_code = http_code
        if message is not None:
            self.message = message
        elif "No workspace with id" in ws_server_err.message:
            self.message = "No Narrative was found with this id."
            self.http_code = 404
        elif "is deleted" in ws_server_err.message:
            self.message = "This Narrative was deleted and is no longer available."
            self.http_code = 410
        elif "may not read" in ws_server_err.message:
            self.message = "You do not have access to this workspace."
            self.http_code = 403
        elif "No object with id" in ws_server_err.message:
            self.message = (
                "Unable to find this Narrative based on workspace information."
            )
            self.http_code = 404
        else:
            self.message = ws_server_err.message

    def __str__(self: "WorkspaceError") -> str:
        return f"WorkspaceError: {self.ws_id}: {self.http_code}: {self.message}"
