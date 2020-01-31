"""
Narrative preprocessor for nbconvert exporting
"""
__author__ = 'Bill Riehl <wjriehl@lbl.gov>'

from nbconvert.preprocessors import Preprocessor
import os
from .processor_util import (
    get_icon,
    get_authors
)
from .app_processor import AppProcessor
from datetime import datetime
from collections import defaultdict
from installed_clients.NarrativeMethodStoreClient import NarrativeMethodStore


class NarrativePreprocessor(Preprocessor):
    def __init__(self, config=None, **kw):
        super(NarrativePreprocessor, self).__init__(config=config, **kw)
        self.host = self.config.narrative_session.host
        base_path = self.config.narrative_session.base_path
        self.style_file = os.path.join(base_path, "static", "styles", "static_narrative.css")
        self.icon_style_file = os.path.join(base_path, "static", "styles", "kbase_icons.css")
        self.assets_base_url = self.config.narrative_session.assets_base_url
        self.assets_version = self.config.narrative_session.assets_version
        self.app_processor = AppProcessor(self.config.narrative_session.ws_url,
                                          self.config.narrative_session.nms_url,
                                          self.config.narrative_session.token)

    def preprocess(self, nb, resources):
        (nb, resources) = super(NarrativePreprocessor, self).preprocess(nb, resources)

        app_meta = self._get_app_metadata(nb, self.config.narrative_session.nms_url)
        narr_data = self.config.narrative_session.narrative_data
        data_types = ", ".join(sorted(narr_data.get("types", {}).keys()))

        # Get some more stuff to show in the page into resources
        if 'kbase' not in resources:
            resources['kbase'] = {}
        resources['kbase'].update({
            'title': nb['metadata']['name'],
            'host': self.host,
            'creator': nb['metadata']['creator'],
            'narrative_link': f"{self.host}/narrative/{nb['metadata']['wsid']}",
            'authors': get_authors(self.config, nb['metadata']['wsid']),
            'service_wizard_url': self.config.narrative_session.service_wizard_url,
            'script_bundle_url': self.assets_base_url + '/js/' + self.assets_version + '/staticNarrativeBundle.js',
            'datestamp': datetime.now().strftime("%B %d, %Y").replace(" 0", " "),
            'logo_url': self.assets_base_url + '/images/kbase-logos/logo-icon-46-46.png',
            'app_citations': app_meta['citations'],
            'meta_keywords': f"{app_meta['meta']}, {data_types}",
            'meta_description': f"A KBase Narrative that uses these Apps: {app_meta['meta']}"
        })

        if 'inlining' not in resources:
            resources['inlining'] = {}
        if 'css' not in resources['inlining']:
            resources['inlining']['css'] = []
        with open(self.style_file, 'r') as css:
            resources['inlining']['css'].append(css.read())
        with open(self.icon_style_file, 'r') as icons:
            icons_file = self.icons_font_css() + icons.read()
            resources['inlining']['css'].append(icons_file)

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
            if 'kbase' in cell.metadata:
                kb_meta = cell.metadata.get('kbase', {})
                if kb_meta.get('type') == 'app' and "app" in kb_meta:
                    apps[kb_meta["app"].get("tag", "dev")].add(kb_meta["app"]["id"])

        citations = defaultdict(dict)
        app_names = set()  # the "metadata" is just a list of unique app names.
        nms = NarrativeMethodStore(url=nms_url)
        for tag in apps:
            nms_inputs = {
                "ids": list(apps[tag]),
                "tag": tag
            }

            try:
                app_infos = nms.get_method_full_info(nms_inputs)
            except Exception as e:
                app_infos = []
            for info in app_infos:
                app_names.add(info["name"])
                if "publications" in info:
                    citations[tag][info["name"]] = info["publications"]

        parsed_citations = list()
        tag_map = {
            "release": "Released Apps",
            "beta": "Apps in Beta",
            "dev": "Apps in development"
        }
        for tag in ["release", "beta", "dev"]:
            if tag in citations:
                parsed_citations.append({"heading": tag_map[tag], "app_list": citations[tag]})
        return {
            "citations": parsed_citations,
            "meta": ", ".join(sorted(app_names))
        }

    def icons_font_css(self) -> str:
        """
        Generates the icon font loading css chunk
        """
        font_url = self.assets_base_url + "/fonts/" + self.assets_version + "/kbase-icons"
        font_css = (
            '@font-face {\n'
            '    font-family: "kbase-icons";\n'
            f'    src:url("{font_url}.eot");\n'
            f'    src:url("{font_url}.eot?#iefix") format("embedded-opentype"),\n'
            f'        url("{font_url}.woff") format("woff"),\n'
            f'        url("{font_url}.ttf") format("truetype"),\n'
            f'        url("{font_url}.svg#kbase-icons") format("svg");\n'
            '    font-weight: normal;\n'
            '    font-style: normal;\n'
            '}\n'
        )
        return font_css

    def preprocess_cell(self, cell, resources, index):
        if 'kbase' in cell.metadata:
            kb_meta = cell.metadata.get('kbase', {})
            kb_info = {
                'type': kb_meta.get('type'),
                'idx': index,
                'attributes': kb_meta.get('attributes', {}),
                'icon': get_icon(self.config, kb_meta)
            }
            if kb_info['type'] == 'app':
                kb_info.update(
                    self.app_processor.process(kb_info, kb_meta)
                )
                kb_info['external_link'] = self.host + kb_info['app']['catalog_url']
            elif kb_info['type'] == 'data':
                kb_info['external_link'] = self.host + '/#dataview/' + \
                                           kb_meta['dataCell']['objectInfo']['ref']
            cell.metadata['kbase'] = kb_info
        else:
            kb_info = {
                'type': 'nonkb'
            }
        if 'kbase' not in resources:
            resources['kbase'] = {}
        if 'cells' not in resources['kbase']:
            resources['kbase']['cells'] = {}
        resources['kbase']['cells'][index] = cell.metadata.get('kbase')
        return cell, resources

