#!/bin/bash

set -e
set -x

# Just exec whatever you throw at it.
# Either CMD in the Dockerfile (default) 
# or a 'command' in docker-compose.yml config
# making it possible to override the command

exec $@
