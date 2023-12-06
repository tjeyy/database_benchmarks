#!/bin/bash

set -e

# Load submodules and install dependencies.
git submodule update --init --recursive --quiet
HYRISE_HEADLESS_SETUP=1 ./hyrise/install_dependencies.sh
pip3 install -r requirements.txt

mkdir -p db_comparison_data

root_dir=$(pwd)
monetdb_home="${root_dir}/db_comparison_data/monetdb"
gp_home="${root_dir}/db_comparison_data/greenplum"

# Build Hyrise binaries and dependency discovery plugin.
cd hyrise
mkdir cmake-build-release && cd cmake-build-release
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-14 -DCMAKE_CXX_COMPILER=clang++-14 ..
make hyriseBenchmarkTPCH hyriseBenchmarkTPCDS  hyriseBenchmarkStarSchema hyriseBenchmarkJoinOrder \
     hyriseServer hyriseDependencyDiscoveryPlugin -j "$(nproc)"

# Build and install MonetDB binaries.
cd ../monetdb
mkdir rel && cd rel
cmake -DCMAKE_INSTALL_PREFIX="$monetdb_home" -DASSERT=OFF -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-14 \
      -DCMAKE_CXX_COMPILER=clang++-14 ..
cmake --build . --target install

# Build and install Greenplum binaries.
cd ../greenplum
gp_dir=$(pwd)
./configure --with-llvm --prefix="$gp_home"
CC=clang-14 CXX=clang++-14 make -j "$(nproc)"
CC=clang-14 CXX=clang++-14 make -j "$(nproc)" install

cd "${gp_home}/bin"
ln -s "${gp_dir}/gpMgmt/bin/gppylib" .
