#!/usr/bin/env bash

python3 -m smtpd -n -c DebuggingServer localhost:25 &
su -c /opt/muesli4/muesli-test muesli