#!/bin/sh
script_dir=$(dirname "$(readlink -f "$0")")
export KB_DEPLOYMENT_CONFIG="$script_dir"/../deploy.cfg
export PYTHONPATH="$script_dir"/../lib:"$PYTHONPATH"

WD=/kb/module/work
if [ -f $WD/token ]; then
    cat $WD/token | xargs python -u "$script_dir"/../lib/StaticNarrative/StaticNarrativeServer.py $WD/input.json $WD/output.json
else
    echo "File $WD/token doesn't exist, aborting."
    exit 1
fi
