FROM python:3.12-alpine
LABEL MAINTAINER KBase Developer

# Install pip requirements
COPY requirements.txt .
COPY requirements-test.txt .

# install python modules one at a time so that all deps get resolved properly
RUN apk --update add build-base python3-dev linux-headers pcre-dev && \
    apk cache clean && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-test.txt && \
    apk del build-base python3-dev linux-headers

COPY ./ /kb/module/
WORKDIR /kb/module
RUN mkdir -p /kb/module/work && \
    chmod -R a+rw /kb/module && \
    mv compile_report.json work/

ENV PYTHONPATH="/kb/module/lib:$PYTHONPATH"

WORKDIR /kb/module
ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD []
