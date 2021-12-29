#!/usr/bin/env bash
if [ -z "$1" ]
then
    echo "usage: hide_lectures.sh 20182"
else
    ssh muesli psql -c UPDATE\\ lectures\\ SET\\ is_visible=False\\ WHERE\\ term=\\\'${1}\\\'\\\; muesli
fi
