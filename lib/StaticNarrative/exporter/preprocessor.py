"""
Narrative preprocessor for nbconvert exporting
"""
__author__ = 'Bill Riehl <wjriehl@lbl.gov>'

from nbconvert.preprocessors import Preprocessor
import os
from .processor_util import (
    build_report_view_data,
    get_icon,
    get_authors
)


class NarrativePreprocessor(Preprocessor):
    def __init__(self, config=None, **kw):
        super(NarrativePreprocessor, self).__init__(config=config, **kw)
        self.host = self.config.narrative_session.host
        base_path = self.config.narrative_session.base_path
        self.app_style_file = os.path.join(base_path, "static", "styles", "app_style.css")
        self.icon_style_file = os.path.join(base_path, "static", "styles", "kbaseIcons.css")
        self.assets_base_url = self.config.narrative_session.assets_base_url

    def preprocess(self, nb, resources):
        (nb, resources) = super(NarrativePreprocessor, self).preprocess(nb, resources)

        # Get some more stuff to show in the page into resources
        if 'kbase' not in resources:
            resources['kbase'] = {}
        resources['kbase'].update({
            'title': nb['metadata']['name'],
            'host': self.host,
            'creator': nb['metadata']['creator'],
            'narrative_link': f"{self.host}/narrative/{nb['metadata']['wsid']}",
            'authors': get_authors(self.config, nb['metadata']['wsid']),
            'service_wizard_url': self.config.narrative_session.service_wizard_url
        })

        if 'inlining' not in resources:
            resources['inlining'] = {}
        if 'css' not in resources['inlining']:
            resources['inlining']['css'] = []
        with open(self.app_style_file, 'r') as css:
            resources['inlining']['css'].append(css.read())
        with open(self.icon_style_file, 'r') as icons:
            icons_file = self.icons_font_css() + icons.read()
            resources['inlining']['css'].append(icons_file)

        return nb, resources

    def icons_font_css(self):
        """
        Generates the icon font loading css chunk
        """
        font_url = self.assets_base_url + "/fonts/kbase-icons"
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
            kb_meta = cell.metadata.get('kbase')
            kb_info = {
                'type': kb_meta.get('type'),
                'idx': index,
                'attributes': kb_meta.get('attributes', {}),
                'icon': get_icon(self.config, kb_meta)
            }
            if kb_info['type'] == 'app':
                kb_info.update(self._process_app_info(kb_info, kb_meta))
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
        resources['foo'] = 'bar'
        resources['kbase']['cells'][index] = cell.metadata.get('kbase')
        return cell, resources

    def _process_app_info(self, kb_info: dict, kb_meta: dict) -> dict:
        """
        Extracts the useful bits of the complicated metadata structure so that the Jinja
        templates don't look like spaghetti with stuff like
        'kbase.appCell.app.spec.info......'
        returns a dict with the updated info.
        """
        kb_info['app'] = {
            'title': kb_meta['attributes']['title'],
            'subtitle': kb_meta['attributes']['subtitle'],
            'version': kb_meta['appCell']['app']['version'],
            'id': kb_meta['appCell']['app']['id'],
            'tag': kb_meta['appCell']['app']['tag'],
            'catalog_url': kb_meta['attributes']['info']['url'],
        }
        kb_info['params'] = {
            'input': [],
            'output': [],
            'parameter': []
        }
        param_values = kb_meta['appCell']['params']
        spec_params = kb_meta['appCell']['app']['spec']['parameters']
        for p in spec_params:
            p['value'] = param_values.get(p['id'])
            p_type = p['ui_class']
            kb_info['params'][p_type].append(p)
        kb_info['output'] = {
            "widget": kb_meta['appCell'].get('exec', {}).get('outputWidgetInfo', {}),
            "result": kb_meta['appCell'].get('exec', {}).get('jobState', {}).get('result', []),
            "report": build_report_view_data(
                          self.config,
                          kb_meta['appCell'].get('exec', {}).get('jobState', {}).get('result', [])
                      )
        }
        kb_info['job'] = {
            'state': "new, and hasn't been started."
        }
        if 'exec' in kb_meta['appCell']:
            kb_info['job']['state'] = self._get_job_state(kb_meta['appCell'])
        return kb_info

    def _get_job_state(self, app_meta):
        job_state = app_meta['exec'].get('jobState', {})
        state = job_state.get('job_state', job_state.get('status', 'unknown'))
        if isinstance(state, list):
            state = state[1]
        return state
