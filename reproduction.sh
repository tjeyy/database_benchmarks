#!/bin/bash

set -e

if [ $# -ne 1 ] && [ $# -ne 2 ]
then
  echo 'Usage: ./reproduction.sh NUMA_NODE [CLIENTS]'
  echo '  NUMA_NODE is the NUMA node ID to bound the experiments to.'
  echo '  CLIENTS is the number of clients to use for the high-load experiments. Defaults to the number of cores'
  echo '          avaible on NUMA node NUMA_NODE * 0.6.'
  exit 1
fi

node_id=$1
num_cpu=$(numactl --hardware | grep "node[[:space:]]${node_id}[[:space:]]cpus" | tail -c +"$(echo "node ${node_id} cpus: " | wc -c)" | wc -w)

num_clients=$((num_cpu * 3 / 5))
if [ $# -eq 2 ]
then
  num_clients=$2
fi

# Load Hyrise submodule, install dependencies.
git submodule update --init --recurive
./hyrise/install_dependencies.sh
pip3 install -r requirements.txt

# Build Hyrise binaries and dependency discovery plugin.
cd hyrise
mkdir cmake-build-release && cd cmake-build-release
# You can configure the compiler via
# `-DCMAKE_C_COMPILER=<c_compiler> -DCMAKE_CXX_COMPILER=<cxx_compiler>`. We used LLVM-14, i.e.,
# `-DCMAKE_C_COMPILER=clang-14 -DCMAKE_CXX_COMPILER=clang++-14`.
cmake -DCMAKE_BUILD_TYPE=Release ..
make hyriseBenchmarkTPCH hyriseBenchmarkTPCDS  hyriseBenchmarkStarSchema hyriseBenchmarkJoinOrder \
     hyriseServer hyriseDependencyDiscoveryPlugin -j "$(nproc)"

# Execute experiments, limited to chosen NUMA node.
# 1. Different optimizations, with and without schema constraints. This will take some hours.
numactl -N "${node_id}" -m "${node_id}" FORCE_CLEAN=false ../scripts/benchmark_single_optimizations.sh HEAD
# 2. Combined optimizations for different scale factors. Running this will take multiple days.
numactl -N "${node_id}" -m "${node_id}" FORCE_CLEAN=false ../scripts/benchmark_compare_plugin_sf.sh HEAD
# 3. Throughput for Hyrise using no optimizations, external rewrites, and the internal optimizer.
#    Expected to take ca. 8h. We expect this to be bound to one NUMA node and the scripts should
#    be limited using numactl. In our experiments, we used 32 clients and 56 logical cores on one
#    NUMA node.
cd ../..
numactl -N "${node_id}" ./scripts/db_comparison_runner.py hyrise --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}"
numactl -N "${node_id}" ./scripts/db_comparison_runner.py hyrise --rewrites --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}"
numactl -N "${node_id}" ./scripts/db_comparison_runner.py hyrise-int --clients "${num_clients}" --cores "${num_cpu}" -m "${node_id}"
cd hyrise/cmake-build-release

# Build and execute naive dependency discovery for comparison.
git checkout benchmark-naive-validation
make hyriseBenchmarkTPCH hyriseBenchmarkTPCDS hyriseBenchmarkStarSchema hyriseBenchmarkJoinOrder \
     hyriseDependencyDiscoveryPlugin -j "$(nproc)"

cd ..
numactl -N "${node_id}" -m "${node_id}" SCHEMA_CONSTRAINTS=0 VALIDATION_LOOPS=100 ./cmake-build-release/hyriseBenchmarkTPCH \
    -r 0 -p ./cmake-build-release/lib/libHyriseDependencyDiscoveryPlugin.so \
    > cmake-build-release/benchmark_plugin_results/hyriseBenchmarkTPCH_st_s10_plugin_naive.log
numactl -N "${node_id}" -m "${node_id}" SCHEMA_CONSTRAINTS=0 VALIDATION_LOOPS=100 ./cmake-build-release/hyriseBenchmarkTPCDS \
    -r 0 -p ./cmake-build-release/lib/libHyriseDependencyDiscoveryPlugin.so \
    > cmake-build-release/benchmark_plugin_results/hyriseBenchmarkTPCDS_st_s10_plugin_naive.log
numactl -N "${node_id}" -m "${node_id}" SCHEMA_CONSTRAINTS=0 VALIDATION_LOOPS=100 ./cmake-build-release/hyriseBenchmarkStarSchema \
    -r 0 -p ./cmake-build-release/lib/libHyriseDependencyDiscoveryPlugin.so \
    > cmake-build-release/benchmark_plugin_results/hyriseBenchmarkStarSchema_st_s10_plugin_naive.log
numactl -N "${node_id}" -m "${node_id}" SCHEMA_CONSTRAINTS=0 VALIDATION_LOOPS=100 ./cmake-build-release/hyriseBenchmarkJoinOrder \
    -r 0 -p ./cmake-build-release/lib/libHyriseDependencyDiscoveryPlugin.so \
    > cmake-build-release/benchmark_plugin_results/hyriseBenchmarkJoinOrder_st_plugin_naive.log

git checkout main

# Create plots.
cd ..
mkdir figures

./scripts/plot_validation_difference.py "$(cd hyrise && git rev-parse HEAD)" -s symlog
./scripts/plot_validation_time.py "$(cd hyrise && git rev-parse HEAD)" -s symlog
./scripts/plot_performance_impact.py "$(cd hyrise && git rev-parse HEAD)" -s symlog
./scripts/plot_tradeoff_sf.py "$(cd hyrise && git rev-parse HEAD)" -s symlog
./scripts/plot_comparison.py
