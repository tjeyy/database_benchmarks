#!/bin/bash

set -e

rm -rf ~/gp_data
rm -rf ~/gpAdminLogs

mkdir ~/gp_data
mkdir ~/gpAdminLogs

./scripts/greenplum_start.sh

./scripts/greenplum_configure.sh
