#!/bin/bash
#
# Use this script to execute commands within the local environment
#
# Usage:
#
# $ ./bin/local.sh make start  # starts uvicorn locally

env $(cat local.env | xargs) $@
