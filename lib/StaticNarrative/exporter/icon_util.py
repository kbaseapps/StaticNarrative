"""Icon-related functions."""

import json
from typing import Any

from traitlets.config import Config

from StaticNarrative import STATIC_NARRATIVE_BASE_DIR

ICON_DATA_FILE = STATIC_NARRATIVE_BASE_DIR / "data" / "icons.json"
ICON_DATA = None


def _load_icon_data() -> None:
    # this should access the local folder
    global ICON_DATA
    try:
        with ICON_DATA_FILE.open() as icon_file:
            ICON_DATA = json.load(icon_file)
    except FileNotFoundError as e:
        msg = f"File {ICON_DATA_FILE} not found."
        raise FileNotFoundError(msg) from e
    except json.JSONDecodeError as e:
        msg = f"File {ICON_DATA_FILE} is not a valid JSON file."
        raise ValueError(msg) from e
    except Exception as e:
        msg = f"An error occurred while loading the file {ICON_DATA_FILE}: {e}"
        raise RuntimeError(msg) from e
    if not ICON_DATA:
        msg = f"No icon data found in {ICON_DATA_FILE}."
        raise ValueError(msg)


def get_data_icon(obj_type: str) -> dict[str, str]:
    """Get the appropriate icon metadata for a specific object type."""
    if not ICON_DATA:
        _load_icon_data()

    # this should not be needed, but is added in to keep python type-checking happy.
    if not ICON_DATA:
        msg = f"No icon data found in {ICON_DATA_FILE}."
        raise ValueError(msg)

    icon_info = {
        "icon": ICON_DATA["data"]["DEFAULT"],
        "color": ICON_DATA["colors"][0],
        "shape": "circle",
    }
    if obj_type in ICON_DATA["data"]:
        icon_info["icon"] = " ".join(ICON_DATA["data"][obj_type])
    if obj_type in ICON_DATA["color_mapping"]:
        icon_info["color"] = ICON_DATA["color_mapping"][obj_type]
    return icon_info


def get_icon(config: Config, metadata: dict[str, Any]) -> dict[str, str]:
    """Should return a dict with keys "type" and "icon".

    * if "type" = image, then "icon" second should be the src.
    * if "type" = class, "icon" should be the full class to use to render the icon -
        "fa fa-right-arrow", for instance.
    * also, if "type" == "class", then the keys "color" and "shape" should also be present.
    """
    icon = {"type": "image", "icon": None}
    if metadata.get("type") == "data":
        icon["type"] = "class"
        icon.update(
            get_data_icon(metadata.get("dataCell", {}).get("objectInfo", {}).get("typeName"))
        )
    elif metadata.get("type") == "output":
        icon["type"] = "class"
        icon["icon"] = "fa-arrow-right"
        icon["color"] = "silver"
        icon["shape"] = "square"
    elif metadata.get("type") == "app":
        if "icon" in metadata.get("appCell", {}).get("app", {}).get("spec", {}).get("info", {}):
            icon["type"] = "image"
            icon["icon"] = (
                config.narrative_session.nms_image_url
                + metadata["appCell"]["app"]["spec"]["info"]["icon"]["url"]
            )
        else:
            icon["type"] = "class"
            icon["icon"] = "fa-cube"
            icon["shape"] = "square"
            icon["color"] = "#673ab7"
    else:
        icon["type"] = "class"
        icon["icon"] = "fa-question-circle-o"
        icon["shape"] = "square"
        icon["color"] = "silver"
    return icon
