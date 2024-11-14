#!/bin/bash

set -e

# Load submodules and install dependencies.
git config --global --add safe.directory "$(pwd)"
git submodule update --init --recursive --quiet
HYRISE_HEADLESS_SETUP=1 ./hyrise/install_dependencies.sh
./install_dependencies.sh
pip3 install -r requirements.txt

mkdir -p db_comparison_data

project_root=$(pwd)
monetdb_home="${project_root}/db_comparison_data/monetdb"
gp_home="${project_root}/db_comparison_data/greenplum"

# Build Hyrise binaries and dependency discovery plugin.
cd hyrise
mkdir -p cmake-build-release && cd cmake-build-release
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-17 -DCMAKE_CXX_COMPILER=clang++-17 ..
make hyriseBenchmarkTPCH hyriseBenchmarkTPCDS  hyriseBenchmarkStarSchema hyriseBenchmarkJoinOrder \
     hyriseServer hyriseDependencyDiscoveryPlugin -j "$(nproc)"

# Build and install MonetDB binaries.
cd "$project_root"/monetdb
mkdir -p rel && cd rel
cmake -DCMAKE_INSTALL_PREFIX="$monetdb_home" -DASSERT=OFF -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-17 \
      -DCMAKE_CXX_COMPILER=clang++-17 ..
cmake --build . --target install -- -j "$(nproc)"

# Download and unpack Umbra binaries.
cd "$project_root"/db_comparison_data
curl "https://db.in.tum.de/~fent/umbra-2024-03-28.tar.xz" -o umbra-2024-03-28.tar.xz
tar xf umbra-2024-03-28.tar.xz
rm umbra-2024-03-28.tar.xz
cd "$project_root"

# Build and install Greenplum binaries.
cd "$project_root"/greenplum
gp_dir=$(pwd)
CC=clang-17 CXX=clang++-17 ./configure --prefix="$gp_home" --disable-gpfdist
CC=clang-17 CXX=clang++-17 make -j "$(nproc)"
CC=clang-17 CXX=clang++-17 make -j "$(nproc)" install
cd "${gp_home}/bin"
ln -s -f "${gp_dir}/gpMgmt/bin/gppylib" .

# Download data for experiments on different systems.
cd "$project_root"
python3 python/helpers/download_data.py
