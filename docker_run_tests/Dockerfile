FROM ubuntu:bionic

RUN mkdir -p /opt/muesli4
WORKDIR /opt/muesli4

ENV PYTHONUNBUFFERED=1
ENV MUESLI_PATH=/opt/muesli4

EXPOSE 8080
CMD ["/opt/muesli4/docker_run_tests/docker-run-tests.sh"]

ENV LANG de_DE.UTF-8
ENV LANGUAGE de_DE:de
ENV LC_ALL de_DE.UTF-8

RUN useradd muesli && \
    DEBIAN_FRONTEND="noninteractive" apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y \
        python3.6 python3.6-dev lp-solve postgresql-server-dev-10 wget \
        python3-pip libjs-prototype libjs-select2.js libjs-jquery-fancybox \
        libjs-jquery-tablesorter locales libpcre3 libpcre3-dev && \
    apt-get install -y --no-install-recommends chromium-chromedriver && \
    rm -rf /var/lib/apt/lists/* && \
    wget https://www.mathi.uni-heidelberg.de/~jvisintini/lp_solve -O /usr/bin/lp_solve && \
    wget https://www.mathi.uni-heidelberg.de/~jvisintini/libxli_DIMACS.so -O /usr/lib/lp_solve/libxli_DIMACS.so && \
    locale-gen de_DE.UTF-8

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt \

COPY --chown=muesli:muesli ./requirements.txt /opt/muesli4/

