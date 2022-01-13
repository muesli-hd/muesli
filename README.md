branch     | build status                                                                                                                 | codecoverage                                                                                                                                                |
-----------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
master     | [![travis master](https://travis-ci.com/muesli-hd/muesli.svg?branch=master)](https://travis-ci.com/muesli-hd/muesli)         | [![codecov master](https://codecov.io/gh/muesli-hd/muesli/branch/master/graph/badge.svg)](https://codecov.io/gh/muesli-hd/muesli/branch/master)             |
production | [![travis production](https://travis-ci.com/muesli-hd/muesli.svg?branch=production)](https://travis-ci.com/muesli-hd/muesli) | [![codecov production](https://codecov.io/gh/muesli-hd/muesli/branch/production/graph/badge.svg)](https://codecov.io/gh/muesli-hd/muesli/branch/production) |

# MÜSLI (Mathematisches Übungsgruppen und Scheinlisten Interface)
MÜSLI is a tool for managing tutorials an exercises used at
the [mathematics and computer science department](https://mathinf.uni-heidelberg.de/de)
of [Universität Heidelberg](https://www.uni-heidelberg.de/de). The production instance is
available [here](https://muesli.mathi.uni-heidelberg.de/).

## Quick Setup:

All MÜSLI development is currently done using Docker and docker-compose. To fire up your own MÜSLI instance, simply
execute the following:

    git clone https://github.com/muesli-hd/muesli.git
    cd muesli
    docker-compose up

If this doesn't work, you could be missing docker or docker-compose. Please visit
the [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/)
installation guides and try the above commands again.

## Contributing
Read more about contributing to this project in the [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Changes
Read more about the changes in this project in the [`CHANGELOG.md`](./CHANGELOG.md).

## Testing
MÜSLI has a test suite to catch bugs before going into production. If you want to execute them, simply use the included
script:

    ./docker/run-tests.sh

It will fire up a docker-compose environment with all required services, run the tests and show you the output.
