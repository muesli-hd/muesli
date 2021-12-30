FROM node:current AS node-build

COPY muesli/web/yarn .

RUN yarn install && \
    yarn dockerbuild


FROM ubuntu:bionic

RUN mkdir -p /opt/muesli4
WORKDIR /opt/muesli4

ENV PYTHONUNBUFFERED=1
ENV MUESLI_PATH=/opt/muesli4

EXPOSE 8080
CMD ["/opt/muesli4/docker-serve.sh"]

ENV LANG de_DE.UTF-8
ENV LANGUAGE de_DE:de
ENV LC_ALL de_DE.UTF-8

RUN useradd muesli && \
    DEBIAN_FRONTEND="noninteractive" apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y \
        python3.6 python3.6-dev lp-solve postgresql-server-dev-10 wget unzip \
        python3-pip libjs-prototype locales libpcre3 libpcre3-dev wait-for-it rsync && \
    rm -rf /var/lib/apt/lists/* && \
    wget https://www.mathi.uni-heidelberg.de/~jvisintini/lp_solve -O /usr/bin/lp_solve && \
    wget https://www.mathi.uni-heidelberg.de/~jvisintini/libxli_DIMACS.so -O /usr/lib/lp_solve/libxli_DIMACS.so && \
    locale-gen de_DE.UTF-8


COPY ./requirements.txt /opt/muesli4/

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt

COPY --from=node-build captcha.min.js muesli/web/static/js/
COPY --from=node-build node_modules/jquery/dist/jquery.min.js muesli/web/static/js/
COPY --from=node-build node_modules/select2/dist/js/select2.min.js muesli/web/static/js/
COPY --from=node-build node_modules/select2/dist/css/select2.min.css muesli/web/static/css/
COPY --from=node-build node_modules/tablesorter/dist/js/jquery.tablesorter.min.js muesli/web/static/js/jquery/
COPY --from=node-build node_modules/@fancyapps/fancybox/dist/jquery.fancybox.min.js muesli/web/static/js/jquery/
COPY --from=node-build node_modules/@fancyapps/fancybox/dist/jquery.fancybox.min.css muesli/web/static/css/
COPY --from=node-build node_modules/@popperjs/core/dist/cjs/popper-base.js muesli/web/static/js/
COPY --from=node-build node_modules/bootstrap/dist/js/bootstrap.min.js muesli/web/static/js/
COPY --from=node-build node_modules/bootstrap/dist/css/bootstrap.min.css muesli/web/static/css/
RUN cp -r muesli/web/static/ /opt/muesli_static_libs
COPY . /opt/muesli4/
