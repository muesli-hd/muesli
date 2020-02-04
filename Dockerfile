FROM ubuntu:bionic

RUN mkdir -p /opt/muesli4
WORKDIR /opt/muesli4

ENV PYTHONUNBUFFERED=1
ENV MUESLI_PATH=/opt/muesli4

EXPOSE 8080
CMD ["/opt/muesli4/docker-serve.sh"]

RUN useradd muesli && \
    apt-get update && \
    apt-get install -y \
        python3.6 python3.6-dev lp-solve postgresql-server-dev-10 wget  \
        python3-pip libjs-prototype libjs-select2.js libjs-jquery-fancybox \
        libjs-jquery-tablesorter locales libpcre3 libpcre3-dev && \
    rm -rf /var/lib/apt/lists/* && \
    locale-gen de_DE.UTF-8 && \
    wget https://www.mathi.uni-heidelberg.de/~jvisintini/lp_solve -O /usr/bin/lp_solve && \
    wget https://www.mathi.uni-heidelberg.de/~jvisintini/libxli_DIMACS.so -O /usr/lib/lp_solve/libxli_DIMACS.so

ENV LANG de_DE.UTF-8
ENV LANGUAGE de_DE:de
ENV LC_ALL de_DE.UTF-8

COPY --chown=muesli:muesli ./requirements.txt /opt/muesli4/
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt
COPY --chown=muesli:muesli . /opt/muesli4/
