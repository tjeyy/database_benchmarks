#!/bin/bash

query=$1

echo "\"${query}\": \"\"\"$(tr -s '\n' ' ' < ~/Documents/phd/dependency-based-optimization/hyrise/third_party/join-order-benchmark/${query}.sql)\"\"\","
