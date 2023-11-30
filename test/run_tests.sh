#!/bin/sh
echo "Removing temp files..."
rm -rf /kb/module/work/tmp/* || true
echo "...done removing temp files."

current_dir=$(dirname "$(readlink -f "$0")")
export KB_DEPLOYMENT_CONFIG="$current_dir"/deploy.cfg
export PYTHONPATH="$current_dir"/../lib:"$PYTHONPATH"

# run without collecting coverage data
# python -m unittest discover -p "*_test.py"

# collect coverage data
pytest \
    --cov=lib/StaticNarrative \
    --cov-config=.coveragerc \
    --cov-report=html \
    --cov-report=xml \
    test
