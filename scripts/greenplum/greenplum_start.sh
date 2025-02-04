#!/bin/bash

set -e

gp_home="$(pwd)/db_comparison_data/greenplum"

GPHOME="${gp_home}" "${gp_home}/bin/gpstart" -d "${gp_home}/data/gpseg-1" -l "${gp_home}/logs" -a
