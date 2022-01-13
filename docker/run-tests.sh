#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

DOCKER_COMPOSE_PROJECT_OPTS=("-p" "muesli-tests" "--project-directory" "${SCRIPT_DIR}/../" "-f" \
 "${SCRIPT_DIR}/../docker-compose.yml" "-f" "${SCRIPT_DIR}/docker-compose.override.yml")

docker-compose "${DOCKER_COMPOSE_PROJECT_OPTS[@]}" up --abort-on-container-exit --exit-code-from muesli --build "$@"
docker-compose "${DOCKER_COMPOSE_PROJECT_OPTS[@]}" down