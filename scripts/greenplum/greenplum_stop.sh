#!/bin/bash

set -e

gp_home="$(pwd)/db_comparison_data/greenplum"

GPHOME="${gp_home}" "${gp_home}/bin/gpstop" -a -d "${gp_home}/data/gpseg-1"
