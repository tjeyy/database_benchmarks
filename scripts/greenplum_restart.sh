#!/bin/bash

set -e

./scripts/greenplum_stop.sh

rm -rf ~/gp_data
rm -rf ~/gpAdminLogs

mkdir ~/gp_data
mkdir ~/gpAdminLogs

./scripts/greenplum_start.sh
