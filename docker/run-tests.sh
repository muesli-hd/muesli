#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

DOCKER_COMPOSE_PROJECT_OPTS=("-p" "muesli-tests" "--project-directory" "${SCRIPT_DIR}/../" "-f" \
 "${SCRIPT_DIR}/../docker-compose.yml" "-f" "${SCRIPT_DIR}/docker-compose.override.yml")

if [[ $# -eq 2 ]] && [[ $1 -eq "--github-actions-image" ]]; then
  cat > docker/docker-compose.github-actions.yml <<-EOFILE
---
version: '3.2'

services:
  muesli:
    image: $2
EOFILE
  cat docker/docker-compose.github-actions.yml

  DOCKER_COMPOSE_PROJECT_OPTS+=( "-f" "${SCRIPT_DIR}/docker-compose.github-actions.yml" )

  docker-compose "${DOCKER_COMPOSE_PROJECT_OPTS[@]}" up --abort-on-container-exit --exit-code-from muesli --no-build "$@"
else
  docker-compose "${DOCKER_COMPOSE_PROJECT_OPTS[@]}" up --abort-on-container-exit --exit-code-from muesli --build "$@"
  docker-compose "${DOCKER_COMPOSE_PROJECT_OPTS[@]}" down
fi
