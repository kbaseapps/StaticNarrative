#!/bin/sh

python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties

if [ -f ./work/token ] ; then
  export KB_AUTH_TOKEN=$(<./work/token)
fi

if [ $# -eq 0 ] ; then
  sh ./scripts/start_server.sh
elif [ "${1}" = "test" ] ; then
  echo "Run Tests"
  sh ./test/run_tests.sh
elif [ "${1}" = "async" ] ; then
  sh ./scripts/run_async.sh
elif [ "${1}" = "bash" ] ; then
  echo "This image only supports sh shells"
  sh
elif [ "${1}" = "sh" ] ; then
  sh
elif [ "${1}" = "report" ] ; then
  echo "The compile report can be found at ./work/compile_report.json"
else
  echo "Unknown command"
fi
