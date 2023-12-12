"""
Describes a Narrative Ref and has utilities for dealing with it.
This is a lightweight version of what's in the Narrative repo - it only handles
just the strings, and doesn't try to figure out Narrative object ids from
Workspace ids.
It also requires that a version is part of the ref.
"""


class NarrativeRef:
    def _less_than_zero(self: "NarrativeRef", number: str | int, name: str) -> int:
        try:
            integer = int(number)
            if integer <= 0:
                raise ValueError
        except (ValueError, TypeError) as e:
            err = f"The Narrative {name} must be an integer > 0, not {number}"
            raise ValueError(err) from e

        return integer

    def __init__(self: "NarrativeRef", ref: str) -> None:
        """
        :param ref: dict with keys wsid, objid, ver (either present or None)
        wsid is required, this will raise a ValueError if it is not present, or not a number
        objid, while required, can be gathered from the wsid. If there are problems with
        fetching the objid, this will raise a ValueError or a RuntimeError. ValueError gets
        raised if the value is invalid, RuntimeError gets raised if it can't be found
        from the workspace metadata.

        ver is not required
        """
        part_name = {"wsid": "workspace ID", "objid": "object ID", "ver": "version"}
        for part in part_name:
            int_version = self._less_than_zero(ref.get(part), part_name[part])
            setattr(self, part, int_version)

    @staticmethod
    def parse(ref: str) -> "NarrativeRef":
        """
        Creates a NarrativeRef from a reference string. Should be numeric.
        This'll fail here if there's < 1 or > 2 slashes.
        Otherwise it'll fail in the main __init__ function if any segment is malformed.
        """
        if ref.count("/") != 2:
            msg = "A Narrative ref must be of the format wsid/objid/ver"
            raise ValueError(msg)
        split_ref = ref.split("/")
        return NarrativeRef(
            {"wsid": split_ref[0], "objid": split_ref[1], "ver": split_ref[2]}
        )

    def __str__(self: "NarrativeRef") -> str:
        ref_str = f"{self.wsid}/{self.objid}"
        if self.ver is not None:
            ref_str = ref_str + f"/{self.ver}"
        return ref_str

    def __eq__(self: "NarrativeRef", other: "NarrativeRef") -> bool:
        return (
            self.wsid == other.wsid
            and self.objid == other.objid
            and self.ver == other.ver
        )
