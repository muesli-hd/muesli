#!/usr/bin/env bash

DOCKERNAME=muesli

exec &> >(tee -a "/var/log/docker/${DOCKERNAME}/redeploy.log")

LOCKDIR="/run/lock/${DOCKERNAME}-update"

function cleanup {
	if rmdir $LOCKDIR; then
		echo "Finished"
	else
		echo "Failed to remove lock directory '$LOCKDIR'"
		exit 1
	fi
}

if mkdir $LOCKDIR; then
	# lockdir entfernen wenn wir fertig sind
	trap "cleanup" EXIT
	
	echo ===========================================================
	echo
	echo Beginning redeploy of ${DOCKERNAME} at $(date)
	echo

	echo "=> docker-compose up --build -d <="
    cd /opt/muesli4
	docker-compose up --build -d
	
	echo
	echo Ended redeploy of ${DOCKERNAME} at $(date)
	echo
	echo ===========================================================


else
	echo "Could not create lock directory '$LOCKDIR'"
	exit 1
fi
