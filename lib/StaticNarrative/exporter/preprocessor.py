"""
Narrative preprocessor for nbconvert exporting
"""
__author__ = "Bill Riehl <wjriehl@lbl.gov>"

import os
from collections import defaultdict
from datetime import datetime

from installed_clients.NarrativeMethodStoreClient import NarrativeMethodStore
from nbconvert.preprocessors import Preprocessor
from StaticNarrative.upa import deserialize

from .app_processor import AppProcessor
from .processor_util import get_authors, get_icon


class NarrativePreprocessor(Preprocessor):
    def __init__(self, config=None, **kw):
        super(NarrativePreprocessor, self).__init__(config=config, **kw)
        self.host = self.config.narrative_session.host
        base_path = self.config.narrative_session.base_path
        self.style_file = os.path.join(
            base_path, "static", "styles", "static_narrative.css"
        )
        self.icon_style_file = os.path.join(
            base_path, "static", "styles", "kbase_icons.css"
        )
        self.assets_base_url = self.config.narrative_session.assets_base_url
        self.assets_version = self.config.narrative_session.assets_version
        self.app_processor = AppProcessor(
            self.host,
            self.config.narrative_session.ws_url,
            self.config.narrative_session.nms_url,
            self.config.narrative_session.token,
        )

    def preprocess(self, nb, resources):
        (nb, resources) = super(NarrativePreprocessor, self).preprocess(nb, resources)

        app_meta = self._get_app_metadata(nb, self.config.narrative_session.nms_url)
        narr_data = self.config.narrative_session.narrative_data
        data_types = ", ".join(sorted(narr_data.get("types", {}).keys()))
        ws_id = self.config.narrative_session.ws_id

        # Get some more stuff to show in the page into resources
        if "kbase" not in resources:
            resources["kbase"] = {}
        resources["kbase"].update(
            {
                "title": nb["metadata"]["name"],
                "host": self.host,
                "creator": nb["metadata"]["creator"],
                "narrative_link": f"{self.host}/narrative/{ws_id}",
                "authors": get_authors(self.config, nb["metadata"]["wsid"]),
                "service_wizard_url": self.config.narrative_session.service_wizard_url,
                "data_ie_url": self.config.narrative_session.data_ie_url,
                "script_bundle_url": self.assets_base_url
                + "/js/"
                + self.assets_version
                + "/staticNarrativeBundle.js",
                "datestamp": datetime.now().strftime("%B %d, %Y").replace(" 0", " "),
                "logo_url": self.assets_base_url
                + "/images/kbase-logos/logo-icon-46-46.png",
                "app_citations": app_meta["citations"],
                "meta_keywords": f"{app_meta['meta']}, {data_types}",
                "meta_description": f"A KBase Narrative that uses these Apps: {app_meta['meta']}",
            }
        )

        if "inlining" not in resources:
            resources["inlining"] = {}
        if "css" not in resources["inlining"]:
            resources["inlining"]["css"] = []
        with open(self.style_file, "r") as css:
            resources["inlining"]["css"].append(css.read())
        with open(self.icon_style_file, "r") as icons:
            icons_file = self.icons_font_css() + icons.read()
            resources["inlining"]["css"].append(icons_file)

        return nb, resources

    def _get_app_metadata(self, nb, nms_url: str) -> dict:
        """
        Returns a structure containing app metadata and citations.
        {
            meta: str,
            citations: [{
                heading: "Released Apps" (some readable str, not just "dev"),
                app_list: {
                    app_name_1: [{
                        link: 'some link',
                        display_text: 'publication_text'
                    }],
                    app_name_2: [{
                        link: 'some other link',
                        display_text: 'other publication'
                    }]
                }
            }]
        }
        """
        # will be tag -> app_id
        apps = defaultdict(set)
        for cell in nb.cells:
            if "kbase" in cell.metadata:
                kb_meta = cell.metadata.get("kbase", {})
                if kb_meta.get("type") == "app" and "app" in kb_meta:
                    apps[kb_meta["app"].get("tag", "dev")].add(kb_meta["app"]["id"])

        citations = defaultdict(dict)
        app_names = set()  # the "metadata" is just a list of unique app names.
        nms = NarrativeMethodStore(url=nms_url)
        for tag in apps:
            nms_inputs = {"ids": list(apps[tag]), "tag": tag}

            try:
                app_infos = nms.get_method_full_info(nms_inputs)
            except Exception as e:
                app_infos = []
            for info in app_infos:
                app_names.add(info["name"])
                if "publications" in info:
                    citations[tag][info["name"]] = info["publications"]

        parsed_citations = []
        tag_map = {
            "release": "Released Apps",
            "beta": "Apps in Beta",
            "dev": "Apps in development",
        }
        for tag in ["release", "beta", "dev"]:
            if tag in citations:
                parsed_citations.append(
                    {"heading": tag_map[tag], "app_list": citations[tag]}
                )
        return {"citations": parsed_citations, "meta": ", ".join(sorted(app_names))}

    def icons_font_css(self) -> str:
        """
        Generates the icon font loading css chunk
        """
        font_url = (
            self.assets_base_url + "/fonts/" + self.assets_version + "/kbase-icons"
        )
        font_css = (
            "@font-face {\n"
            '    font-family: "kbase-icons";\n'
            f'    src:url("{font_url}.eot");\n'
            f'    src:url("{font_url}.eot?#iefix") format("embedded-opentype"),\n'
            f'        url("{font_url}.woff") format("woff"),\n'
            f'        url("{font_url}.ttf") format("truetype"),\n'
            f'        url("{font_url}.svg#kbase-icons") format("svg");\n'
            "    font-weight: normal;\n"
            "    font-style: normal;\n"
            "}\n"
        )
        return font_css

    def _get_data_cell_ref(self, meta: dict, ws_id: int = None) -> str:
        """
        Returns the object reference inside a data cell, if present.
        If not present, or not creatable from the metadata, returns None.
        If there's an upas set, use that, and cast it to the current workspace
            (and verify the object is there?)
        Otherwise, if there's "objectInfo", use that.
        """
        if "dataCell" not in meta:
            return None
        meta = meta["dataCell"]
        ref = None
        if "upas" in meta and ws_id is not None:
            refs = [deserialize(u, ws_id) for u in meta["upas"].values()]
            ref = refs[0]
        elif "objectInfo" in meta:
            obj_info = meta["objectInfo"]
            if "ref" in obj_info:
                ref = obj_info["ref"]
            else:
                if ("ws_id" in obj_info or "wsid" in obj_info) and "id" in obj_info:
                    ref = f"{obj_info.get('ws_id', obj_info.get('wsid'))}/{obj_info['id']}"
                    if "version" in obj_info:
                        ref = f"{ref}/{obj_info['version']}"
        else:
            return None
        return ref

    def preprocess_cell(self, cell, resources: dict, index: int):
        ws_id = self.config.narrative_session.ws_id

        if "kbase" in cell.metadata:
            kb_meta = cell.metadata.get("kbase", {})
            kb_info = {
                "type": kb_meta.get("type"),
                "idx": index,
                "attributes": kb_meta.get("attributes", {}),
                "icon": get_icon(self.config, kb_meta),
            }
            if kb_info["type"] == "app":
                kb_info.update(self.app_processor.process(kb_info, kb_meta))
                kb_info["external_link"] = self.host + kb_info["app"]["catalog_url"]
            elif kb_info["type"] == "data":
                ref = self._get_data_cell_ref(kb_meta, ws_id)
                if ref is not None:
                    kb_info["external_link"] = f"{self.host}/#dataview/{ref}"
            cell.metadata["kbase"] = kb_info
        else:
            kb_info = {"type": "nonkb"}
        if "kbase" not in resources:
            resources["kbase"] = {}
        if "cells" not in resources["kbase"]:
            resources["kbase"]["cells"] = {}
        resources["kbase"]["cells"][index] = cell.metadata.get("kbase")
        return cell, resources
