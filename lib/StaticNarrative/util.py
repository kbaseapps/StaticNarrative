"""This module contains some utility functions for the SetAPI."""

import re
from typing import Any

UPA_REGEX = re.compile(r"^((\d+)|[A-Za-z].*)\/((\d+)|[A-Za-z].*)(\/\d+)?$")


def check_reference(ref: str) -> bool:
    """Check whether a ref looks like a KBase UPA.

    Returns True if ref looks like an actual object reference: xx/yy/zz or xx/yy.
    Returns False otherwise.
    """
    if ref is None or not UPA_REGEX.match(ref):
        return False
    return True


def build_ws_obj_selector(ref: str, ref_path_to_set: list[str]) -> dict[str, str]:
    """Build a KBase UPA for an object."""
    if ref_path_to_set and len(ref_path_to_set) > 0:
        return {"ref": ";".join(ref_path_to_set)}
    return {"ref": ref}


def populate_item_object_ref_paths(
    set_items: list[dict[str, Any]], obj_selector: dict[str, Any]
) -> list[dict[str, Any]]:
    """Called when include_set_item_ref_paths is set.

    Add a field ref_path to each item in set.
    """
    for set_item in set_items:
        set_item["ref_path"] = obj_selector["ref"] + ";" + set_item["ref"]
    return set_items
