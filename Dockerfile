FROM node:current
COPY muesli/web/yarn .
RUN yarn install
RUN yarn dockerbuild


FROM ubuntu:bionic

RUN mkdir -p /opt/muesli4
WORKDIR /opt/muesli4

ENV PYTHONUNBUFFERED=1
ENV MUESLI_PATH=/opt/muesli4

EXPOSE 8080
CMD ["/opt/muesli4/docker-serve.sh"]

RUN useradd muesli

RUN apt-get update && \
DEBIAN_FRONTEND="noninteractive" apt-get install -y python3 python3-dev lp-solve \
postgresql-server-dev-10 wget python3-pip libjs-prototype \
libjs-select2.js libjs-jquery-fancybox libjs-jquery-tablesorter \
locales libpcre3 libpcre3-dev && \
rm -rf /var/lib/apt/lists/*

RUN locale-gen de_DE.UTF-8
ENV LANG de_DE.UTF-8
ENV LANGUAGE de_DE:de
ENV LC_ALL de_DE.UTF-8

RUN wget https://www.mathi.uni-heidelberg.de/~jvisintini/lp_solve -O /usr/bin/lp_solve
RUN wget https://www.mathi.uni-heidelberg.de/~jvisintini/libxli_DIMACS.so -O /usr/lib/lp_solve/libxli_DIMACS.so


RUN pip3 install --upgrade pip
COPY --chown=muesli:muesli ./requirements.txt /opt/muesli4/
RUN pip3 install -r requirements.txt
COPY --chown=muesli:muesli . /opt/muesli4/
COPY --from=0 captcha.min.js muesli/web/static/js/
