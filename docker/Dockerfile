FROM node:current AS node-build

COPY muesli/web/yarn .

RUN yarn install && \
    yarn dockerbuild


FROM debian:11

RUN mkdir -p /opt/muesli4
WORKDIR /opt/muesli4

ENV PYTHONUNBUFFERED=1
ENV MUESLI_PATH=/opt/muesli4

EXPOSE 8080
CMD ["/opt/muesli4/docker/docker-serve.sh"]

ENV LANG de_DE.UTF-8
ENV LANGUAGE de_DE:de
ENV LC_ALL de_DE.UTF-8
ENV MPLCONFIGDIR /opt/matplotlib_config

RUN useradd muesli && install -d -m 0755 -o muesli -g muesli /opt/matplotlib_config && \
    DEBIAN_FRONTEND="noninteractive" apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        python3.9 lp-solve wget unzip rsync build-essential pkg-config python3-setuptools locales \
        python3-pip libpcre3 uwsgi uwsgi-plugin-python3 iproute2 \
        python3.9-dev python3-yaml postgresql-server-dev-all libpcre3-dev libcairo2-dev libgirepository1.0-dev && \
    rm -rf /var/lib/apt/lists/* && \
    wget https://www.mathi.uni-heidelberg.de/~jvisintini/lp_solve -O /usr/bin/lp_solve && \
    wget https://www.mathi.uni-heidelberg.de/~jvisintini/libxli_DIMACS.so -O /usr/lib/lp_solve/libxli_DIMACS.so && \
    sed -i '/de_DE.UTF-8/s/^# //g' /etc/locale.gen && locale-gen


COPY ./requirements.txt /opt/muesli4/

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install  -r requirements.txt

COPY --from=node-build captcha.min.js \
                       node_modules/jquery/dist/jquery.min.js \
                       node_modules/select2/dist/js/select2.min.js \
                       node_modules/tablesorter/dist/js/jquery.tablesorter.min.js \
                       node_modules/@fancyapps/ui/dist/fancybox.umd.js \
                       node_modules/popper.js/dist/umd/popper.min.js \
                       node_modules/bootstrap/dist/js/bootstrap.min.js \
                       node_modules/bs4-toast/dist/toast.min.js \
                        muesli/web/static/js/
COPY --from=node-build node_modules/select2/dist/css/select2.min.css \
                       node_modules/@fancyapps/ui/dist/fancybox.css \
                       node_modules/bootstrap/dist/css/bootstrap.min.css \
                       node_modules/bs4-toast/dist/toast.min.css \
                        muesli/web/static/css/
RUN cp -r muesli/web/static/ /opt/muesli_static_libs
COPY . /opt/muesli4/
