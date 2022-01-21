#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

DOCKER_COMPOSE_PROJECT_OPTS=("-p" "muesli-tests" "--project-directory" "${SCRIPT_DIR}/../" "-f" \
 "${SCRIPT_DIR}/../docker-compose.yml")

if [[ $# -eq 2 ]] && [[ $1 == "--github-actions-image" ]]; then
  cat > docker/docker-compose.github-actions.yml <<-EOFILE
---
version: '3.2'

services:
  muesli:
    image: $2
    volumes:
      - ./docker/.coverage.xml:/opt/muesli4/docker/.coverage.xml
    command: ["/opt/muesli4/docker/docker-testscript.sh"]
EOFILE

  DOCKER_COMPOSE_PROJECT_OPTS+=( "-f" "${SCRIPT_DIR}/docker-compose.github-actions.yml" )

  # Remove the first two script arguments
  set -- "${@:3}"
  docker-compose "${DOCKER_COMPOSE_PROJECT_OPTS[@]}" --no-ansi up --abort-on-container-exit --exit-code-from muesli --no-build "$@" muesli
else
  docker-compose "${DOCKER_COMPOSE_PROJECT_OPTS[@]}" "-f" "${SCRIPT_DIR}/docker-compose.override.yml" up --abort-on-container-exit --exit-code-from muesli --build "$@" muesli
  docker-compose "${DOCKER_COMPOSE_PROJECT_OPTS[@]}" "-f" "${SCRIPT_DIR}/docker-compose.override.yml" down
fi
