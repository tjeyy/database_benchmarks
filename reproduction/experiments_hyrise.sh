#!/bin/bash

set -e

if [ $# -ne 1 ]; then
  echo 'Usage: ./experiments_hyrise.sh NUMA_NODE'
  echo '  NUMA_NODE is the NUMA node ID to bind the experiments to.'
  exit 1
fi

node_id=$1
numactl_command=""
if [ "$node_id" -ne "-1" ]; then
  numactl_command="numactl -N ${node_id} -m ${node_id}"
fi

# Execute experiments, limited to chosen NUMA node.
cd hyrise/cmake-build-release
# 1. Different optimizations, with and without schema constraints. This will take some hours.
FORCE_CLEAN=false $numactl_command ../scripts/benchmark_single_optimizations.sh HEAD
# 2. Combined optimizations for different scale factors. Running this will take multiple days.
FORCE_CLEAN=false $numactl_command ../scripts/benchmark_compare_plugin_sf.sh HEAD
