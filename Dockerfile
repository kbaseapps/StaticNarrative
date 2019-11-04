FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update
RUN pip install nbconvert==5.6.0 \
    nbformat==4.4.0 \
    traitlets==4.3.3 \
    coverage==4.5.3 \
    pytest-cov==2.8.1 \
    pytest==4.0.2 \
    flake8==3.5.0 \
    coveralls==1.8.2 \
    requests-mock==1.7.0 \
    jsonrpcbase==0.2.0


# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
