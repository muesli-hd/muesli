FROM ubuntu:xenial

RUN mkdir -p /opt/muesli4
WORKDIR /opt/muesli4

ENV PYTHONUNBUFFERED=1
ENV MUESLI_PATH=/opt/muesli4

EXPOSE 8080
CMD ["/opt/muesli4/muesli-test"]

RUN adduser -D -U muesli

RUN apt-get update && apt-get install -y python3.5 python3.5-dev lp-solve postgresql-server-dev-9.5 wget python-pip python-all-dev python3-pip libjs-jquery-fancybox && rm -rf /var/lib/apt/lists/*
RUN wget https://www.mathi.uni-heidelberg.de/~jvisintini/lp_solve -O /usr/bin/lp_solve
RUN wget https://www.mathi.uni-heidelberg.de/~jvisintini/libxli_DIMACS.so -O /usr/lib/lp_solve/libxli_DIMACS.so

COPY --chown=muesli:muesli ./requirements.txt /opt/muesli4
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

USER muesli:muesli

COPY --chown=muesli:muesli ./ /usr/src/app
RUN cp muesli.yml.example muesli.yml
