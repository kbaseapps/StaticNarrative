#!/bin/sh
echo "Removing temp files..."
rm -rf /kb/module/work/tmp/* || true
echo "...temp files removed!"

current_dir=$(dirname "$(readlink -f "$0")")
export KB_DEPLOYMENT_CONFIG="$current_dir"/deploy.cfg
export PYTHONPATH="$current_dir"/../lib:"$PYTHONPATH"

# run without collecting coverage data
# pytest -vv test

# collect coverage data
pytest \
    --cov=lib/StaticNarrative \
    --cov-config=.coveragerc \
    --cov-report=html \
    --cov-report=xml \
    test
