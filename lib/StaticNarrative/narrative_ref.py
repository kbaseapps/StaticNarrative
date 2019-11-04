"""
Describes a Narrative Ref and has utilities for dealing with it.
This is a lightweight version of what's in the Narrative repo - it only handles
just the strings, and doesn't try to figure out Narrative object ids from
Workspace ids.
It also requires that a version is part of the ref.
"""


class NarrativeRef:
    def __init__(self, ref: str):
        """
        :param ref: dict with keys wsid, objid, ver (either present or None)
        wsid is required, this will raise a ValueError if it is not present, or not a number
        objid, while required, can be gathered from the wsid. If there are problems with
        fetching the objid, this will raise a ValueError or a RuntimeError. ValueError gets
        raised if the value is invalid, RuntimeError gets raised if it can't be found
        from the workspace metadata.

        ver is not required
        """
        (self.wsid, self.objid, self.ver) = (ref.get("wsid"), ref.get("objid"), ref.get("ver"))
        try:
            self.wsid = int(self.wsid)
        except ValueError:
            err = f"A numerical Workspace id is required for a Narrative ref, not {self.wsid}"
            raise ValueError(err)

        if self.ver is not None:
            try:
                self.ver = int(self.ver)
            except ValueError:
                err = f"If ver is present in the ref, it must be numerical, not {self.ver}"
                raise ValueError(err)
        if self.objid is not None:
            try:
                self.objid = int(self.objid)
            except ValueError:
                raise ValueError("objid must be numerical, not {}".format(self.objid))
        else:
            raise ValueError("objid is required")

    @staticmethod
    def parse(ref: str):
        """
        Creates a NarrativeRef from a reference string. Should be numeric.
        This'll fail here if there's < 1 or > 2 slashes.
        Otherwise it'll fail in the main __init__ function if any segment is malformed.
        """
        if ref.count("/") != 2:
            raise ValueError("A Narrative ref must be of the format wsid/objid/ver")
        split_ref = ref.split("/")
        return NarrativeRef({
            "wsid": split_ref[0],
            "objid": split_ref[1],
            "ver": split_ref[2]
        })

    def __str__(self) -> str:
        ref_str = "{}/{}".format(self.wsid, self.objid)
        if self.ver is not None:
            ref_str = ref_str + "/{}".format(self.ver)
        return ref_str

    def __eq__(self, other) -> bool:
        return self.wsid == other.wsid and \
               self.objid == other.objid and \
               self.ver == other.ver
