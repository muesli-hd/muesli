FROM ubuntu:bionic

RUN mkdir -p /opt/muesli4
WORKDIR /opt/muesli4

ENV PYTHONUNBUFFERED=1
ENV MUESLI_PATH=/opt/muesli4

EXPOSE 8080

RUN useradd muesli

RUN apt-get update && \
apt-get install -y python3.6 python3.6-dev lp-solve \
postgresql-server-dev-10 wget python3-pip libjs-prototype \
libjs-select2.js libjs-jquery-fancybox libjs-jquery-tablesorter locales && \
apt-get install -y --no-install-recommends chromium-chromedriver && \
rm -rf /var/lib/apt/lists/*

RUN wget https://www.mathi.uni-heidelberg.de/~jvisintini/lp_solve -O /usr/bin/lp_solve
RUN wget https://www.mathi.uni-heidelberg.de/~jvisintini/libxli_DIMACS.so -O /usr/lib/lp_solve/libxli_DIMACS.so

RUN locale-gen de_DE.UTF-8
ENV LANG de_DE.UTF-8
ENV LANGUAGE de_DE:de
ENV LC_ALL de_DE.UTF-8

CMD ["/opt/muesli4/docker_run_tests/docker-run-tests.sh"]

RUN pip3 install --upgrade pip
COPY --chown=muesli:muesli ./requirements.txt /opt/muesli4/
RUN pip3 install -r requirements.txt
