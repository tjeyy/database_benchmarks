#!/bin/bash

set -e

./scripts/greenplum_stop.sh

./scripts/greenplum_init.sh
