#!/bin/bash

query=$1

echo "\"${query}\": \"\"\"$(tr -s '\n' ' ' < "$(pwd)"/hyrise/third_party/join-order-benchmark/"${query}".sql)\"\"\","
