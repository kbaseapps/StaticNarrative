{%- extends 'narrative_basic.tpl' -%}
{% from 'mathjax.tpl' import mathjax %}


{%- block header -%}
<!DOCTYPE html>
<html>
<head>
{%- block html_head -%}
<meta charset="utf-8" />
<title>KBase Narrative - {{ resources['kbase']['title'] }}</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
<script src="./dataBrowser.js"></script>

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<style type="text/css">
/* Overrides of notebook CSS for static HTML export */
body {
  overflow: visible;
  padding: 8px;
}

div#notebook {
  overflow: visible;
  border-top: none;
}

@media print {
  div.cell {
    display: block;
    page-break-inside: avoid;
  }
  div.output_wrapper {
    display: block;
    page-break-inside: avoid;
  }
  div.output {
    display: block;
    page-break-inside: avoid;
  }
}
</style>

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.css">
<!-- Loading mathjax macro -->
{{ mathjax() }}

{# <script src="{{ resources['kbase']['host'] }}/static/narrative_paths.js"></script> #}
{# <script>
    require.config({
        baseUrl: "{{ resources['kbase']['host'] }}/static/",
        paths: {
            jquery: 'components/jquery/jquery-min',
            underscore : 'components/underscore/underscore-min',
            backbone : 'components/backbone/backbone-min',
            bootstrap: 'components/bootstrap/js/bootstrap.min',
            'jquery-ui': 'components/jquery-ui/jquery-ui.min',
            kbaseAuthenticatedWidget: 'kbase/js/widgets/kbaseStaticAuthenticatedWidget'
        },
        shim: {
            underscore: {
                exports: '_'
            },
            backbone: {
                deps: ["underscore", "jquery"],
                exports: "Backbone"
            },
            bootstrap: {
                deps: ["jquery"],
                exports: "bootstrap"
            },
            'jquery-ui': {
                deps: ['jquery'],
                exports: '$'
            }
        },
        map: {
            '*':{
                'jqueryui': 'jquery-ui',
            }
        }
    });
</script> #}
{%- endblock html_head -%}
</head>
{%- endblock header -%}

<body>
{% block body %}
  <div class="container">
    <div class="kbs-header">
      <div>
        <div class="kbs-title"><a href="{{ resources.kbase.narrative_link }}">{{ resources.kbase.title }}</a></div>
        <div class="kb-author-list">
          {%- for author in resources['kbase']['authors'] -%}
            <a href="{{ author.path }}">{{ author.name }}</a>
            {%- if not loop.last -%}, {% endif -%}
          {%- endfor -%}
        </div>
      </div>
      <div class="branding">
        <img src="https://ci.kbase.us/modules/plugins/mainwindow/resources/images/kbase_logo.png"/>
        <div>Generated {{ resources.kbase.datestamp }}</div>
      </div>
    </div>
  </div>

  <div tabindex="-1" id="notebook" class="border-box-sizing">
    <div class="container">
      <ul class="kbs-tabs nav nav-tabs" role="tablist">
        <li role="presentation" class="active">
          <a href="#kbs-narrative" aria-controls="kbs-narrative" role="tab" data-toggle="tab">Narrative</a>
        </li>
        <li role="presentation">
          <a href="#kbs-data" aria-controls="kbs-data" role="tab" data-toggle="tab">Data</a>
        </li>
        <li role="presentation">
          <a href="#kbs-citations" aria-controls="kbs-citations" role="tab" data-toggle="tab">Citations</a>
        </li>
      </ul>
      <div class="tab-content" id="notebook-container">
        <div role="tabpanel" class="tab-pane active" id="kbs-narrative">
          {{ super() }}
        </div>
        <div role="tabpanel" class="tab-pane" id="kbs-data"></div>
        <div role="tabpanel" class="tab-pane" id="kbs-citations"></div>
      </div>
    </div>
  </div>

  <script>

  function selectTab(tabId) {
    // get the tab and panel, make sure they're real.
    const tab = document.querySelector('.kbs-tabs [href="#' + tabId + '"]').parentElement;
    if (tab.classList.contains('active')) {
      return;
    }
    const tabPanel = document.querySelector('.tab-content [id="' + tabId + '"]');
    if (tab && tabPanel) {
      // set all tabs inactive, activate given tab.
      document.querySelectorAll('.kbs-tabs > li').forEach(node => node.classList.remove('active'));
      tab.classList.add('active');
      // set all tabPanels inactive, activate given one.
      document.querySelectorAll('.tab-content[id="notebook-container"] > div[role="tabpanel"]').forEach((node) => {
        node.classList.remove('active');
        node.classList.add('kbs-is-hidden');
      });
      tabPanel.classList.add('active');
      tabPanel.classList.remove('kbs-is-hidden');
    }
  }

  function toggleAppView(btn) {
    const appIdx = btn.dataset.idx;
    const id = 'app-' + appIdx;
    const view = btn.dataset.view;
    document.querySelectorAll('div[id^="' + id + '"]').forEach(node => {
      node.hidden = true;
    });
    document.querySelectorAll('button.app-view-toggle[data-idx="' + appIdx + '"]').forEach(node => {
      node.classList.remove('selected');
    });
    document.querySelector('div[id^="' + id + '-' + view + '"]').hidden = false;
    btn.classList.add('selected');
  }

  let fileSetServUrl = null,
      lastFSSUrlLookup = 0,
      dataBrowser = null;

  function getFileServUrl(servWizardUrl) {
    const now = new Date();
    const fiveMin = 300000;  //ms
    if (fileSetServUrl == null || now.getTime() > lastFSSUrlLookup + fiveMin) {
      return fetch(servWizardUrl, {
        method: 'POST',
        mode: 'cors',
        cache: 'no-cache',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          method: 'ServiceWizard.get_service_status',
          params: [{
            module_name: 'HTMLFileSetServ',
            version: null
          }],
          version: '1.1',
          id: String(Math.random()).slice(2)
        })
      })
      .then(response => response.json())
      .then((res) => {
        fileSetServUrl = res.result[0].url;
        return fileSetServUrl;
      });
    }
    else {
      return new Promise((resolve) => {
        resolve(fileSetServUrl);
      });
    }
  }
  getFileServUrl("https://ci.kbase.us/services/service_wizard")
    .then((fssUrl) => {
      document.querySelectorAll('div.kb-app-report').forEach((node) => {
        const reportUrl = fssUrl + node.dataset.path;
        const iframe = document.createElement('iframe');
        iframe.setAttribute('id', 'iframe-' + String(Math.random()).slice(2));
        iframe.classList.add('kb-app-report-iframe');
        node.appendChild(iframe);
        iframe.setAttribute('src', reportUrl);
      });
    });

  // init main tab events
  document.querySelectorAll('.kbs-tabs a').forEach((node) => {
    node.addEventListener('click', (e) => {
      e.preventDefault();
      selectTab(node.getAttribute('href').slice(1));
    });
  });

  // init data browser on click
  document.querySelector('a[href="#kbs-data"]').addEventListener('click', event => {
    if (!dataBrowser) {
      dataBrowser = new DataBrowser({
        node: document.querySelector('div#kbs-data'),
        dataFile: 'data.json'
      });
    }
  });

  // init app cell tab events
  document.querySelectorAll('button.app-view-toggle').forEach((node) => {
    node.addEventListener('click', (e) => {
      toggleAppView(node);
    });
  });

  </script>
{% endblock body %}
</body>

{% block footer %}
{% endblock footer %}
</html>
