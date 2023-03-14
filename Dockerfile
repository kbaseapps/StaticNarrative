#FROM kbase/sdkbase2:python


FROM python:3.10-alpine
LABEL MAINTAINER KBase Developer

COPY ./requirements.txt /kb/module/
COPY ./requirements-dev.txt /kb/module/
WORKDIR /kb/module

# install python modules one at a time so that all deps get resolved properly
RUN pip install --upgrade pip && \
    cat requirements.txt | sed -e '/^\s*#.*$/d' -e '/^\s*$/d' | xargs -n 1 pip install && \
    cat requirements-test.txt | sed -e '/^\s*#.*$/d' -e '/^\s*$/d' | xargs -n 1 pip install && \
    mkdir -p /kb/module/work && \
    chmod -R a+rw /kb/module

ENV PYTHONPATH="/kb/module/lib:$PYTHONPATH"
COPY ./ /kb/module/

WORKDIR /kb/module
ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD []
