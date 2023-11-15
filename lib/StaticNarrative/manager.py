import os
from collections import defaultdict
from typing import T


class StaticNarrativeManager:
    def __init__(self: "StaticNarrativeManager", config: dict[str, T]) -> None:
        self.config = config

    def list_static_narratives(
        self: "StaticNarrativeManager",
    ) -> dict[str, dict[str, str]]:
        """
        Returns a list of all available static narratives.
        Currently, this combs the filesystem for index.html files and assembles them.
        Later, this'll make a call to MongoDB.
        """
        webroot = self.config["static-file-root"]
        if webroot is None:
            raise ValueError("Missing path to static narratives")
        all_sn = defaultdict(list)
        for root, _, files in os.walk(webroot):
            for name in files:
                if name != "index.html":
                    continue
                print(root)
                (ws_id, ver) = root.split("/")[-2:]
                all_sn[ws_id].append(
                    {
                        "ws_id": ws_id,
                        "narrative_version": ver,
                        "url": f"/{ws_id}/{ver}/",
                    }
                )
        return dict(all_sn)
