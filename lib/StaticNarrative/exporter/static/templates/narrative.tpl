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
        <div role="tabpanel" class="tab-pane" id="kbs-citations">
          {%- for app_block in resources.kbase.app_citations -%}
            {%- if resources.kbase.app_citations | length == 1 -%}
            <h3>Apps</h3>
            {%- else -%}
            <h3>{{ app_block.heading }}</h3>
            {% endif %}
            <ol>
            {%- for app in app_block.app_list|sort()-%}
              <li>
                <div><b>{{ app }}</b></div>
                {% if app_block.app_list[app]|length > 0 %}
                  <ul>
                    {%- for citation in app_block.app_list[app] -%}
                      <li>
                        {{ citation.display_text }}
                        {%- if citation.link -%}
                        <a href="{{ citation.link }}"><span class="fa fa-external-link"></span></a>
                        {% endif %}
                      </li>
                    {% endfor %}
                  </ul>
                {% else %}
                  <div>no citations</div>
                {% endif %}
              </li>
            {%- endfor -%}
            </ol>
          {%- endfor -%}
        </div>
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
