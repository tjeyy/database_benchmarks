#!/bin/bash

set -e

if [ $# -ne 3 ]; then
  echo 'Usage: ./experiments_systems.sh NUMA_NODE NUM_CPU NUM_CLIENTS'
  echo '  NUMA_NODE is the NUMA node ID to bind the experiments to.'
  echo '  NUM_CPU is the number of logical cores the DBMSs can use.'
  echo '  NUM_CLIENTS is the number of clients that query the DBMSs.'
  exit 1
fi

node_id=$1
num_cpu=$2
num_clients=$3

numactl_command="numactl -N ${node_id}"
no_numa=""

if [ "$node_id" -eq "-1" ]; then
  numactl_command=""
  no_numa="--no_numactl"
fi

# Throughput for different systems using no optimizations, external rewrites, and the internal optimizer. Expected to
# take ca. 8h. We expect this to be bound to one NUMA node and the scripts should be limited using numactl. In our
# experiments, we used 32 clients and 56 logical cores on one NUMA node.
$numactl_command ./python/db_comparison_runner.py hyrise --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" "${no_numa}"
$numactl_command ./python/db_comparison_runner.py hyrise --rewrites --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" "${no_numa}"
$numactl_command ./python/db_comparison_runner.py hyrise-int --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" "${no_numa}"
$numactl_command ./python/db_comparison_runner.py monetdb --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" "${no_numa}"
$numactl_command ./python/db_comparison_runner.py monetdb --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" --skip_data_loading "${no_numa}"
$numactl_command ./python/db_comparison_runner.py umbra --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" "${no_numa}"
$numactl_command ./python/db_comparison_runner.py umbra --rewrites --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" "${no_numa}"

num_segments=$([ "$num_cpu" -le 14 ] && echo "$num_cpu" || echo "14")
./python/greenplum_configure.py -p 7777 -n "$num_segments"
PORT=7777 ./scripts/greenplum_init.sh
$numactl_command ./python/db_comparison_runner.py greenplum --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" "${no_numa}" -p 7777
$numactl_command ./python/db_comparison_runner.py greenplum --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}" --skip_data_loading "${no_numa}" -p 7777
./scripts/greenplum_stop.sh
