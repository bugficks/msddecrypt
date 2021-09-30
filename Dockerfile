########################################################################################################################
#
FROM python:2-alpine AS base

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    PYTHONDONTWRITEBYTECODE=1

RUN apk update
RUN apk add --no-cache --virtual .build-deps \
    alpine-sdk openssl-dev python2-dev libffi-dev

RUN apk add --no-cache --virtual .run-deps \
    tzdata bash coreutils busybox-extras # git vim make curl openssl

RUN echo $TZ > /etc/timezone \
    && cp /usr/share/zoneinfo/$TZ /etc/localtime

WORKDIR /opt/app
COPY requirements.txt /opt/app/
RUN pip install -r requirements.txt
ADD src /opt/app/

RUN apk del tzdata .build-deps \
    && rm -rf /var/cache/apk* /tmp/* /var/tmp/*

########################################################################################################################
#
FROM scratch

ENV TZ=Etc/UTC
COPY --from=base / /

WORKDIR /opt
ENTRYPOINT [ "python2", "/opt/app/msddecrypt.py" ]
