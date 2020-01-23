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
        <img src="{{ resources.kbase.logo_url }}"/>
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

  <script type="text/javascript" src="{{ resources.kbase.script_bundle_url }}" crossorigin="anonymous"></script>
  <script>
    initStaticNarrative("{{ resources.kbase.service_wizard_url }}")
  </script>
{% endblock body %}
</body>

{% block footer %}
{% endblock footer %}
</html>
