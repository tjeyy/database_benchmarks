#!/bin/bash

set -e
set -x

# Load submodules and install dependencies.
git config --global --add safe.directory "$(pwd)"
git submodule update --init --recursive
HYRISE_HEADLESS_SETUP=1 ./hyrise/install_dependencies.sh
./install_dependencies.sh
pip3 install -r requirements.txt --break-system-packages

mkdir -p db_comparison_data

project_root=$(pwd)
monetdb_home="${project_root}/db_comparison_data/monetdb"
gp_home="${project_root}/db_comparison_data/greenplum"
umbra_home="${project_root}/db_comparison_data/umbra"

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

rces.list.d/docker.list > /dev/null
sudo apt-get update

sudo systemctl start docker

# Fetch Umbra docker image.
cd "$project_root"
mkdir -p "$umbra_home"
chmod 777 "$umbra_home"
docker pull umbradb/umbra:24.11

sudo systemctl stop docker docker.socket

# Build and install Greenplum binaries.
cd "$project_root"/greenplum
gp_dir=$(pwd)
CC=gcc-11 CXX=g++-11 ./configure --prefix="$gp_home" --disable-gpfdist
CC=gcc-11 CXX=g++-11 make -j "$(nproc)"
CC=gcc-11 CXX=g++-11 make -j "$(nproc)" install
cd "${gp_home}/bin"
ln -s -f "${gp_dir}/gpMgmt/bin/gppylib" .

# Download data for experiments on different systems.
cd "$project_root"
python3 python/helpers/download_data.py
