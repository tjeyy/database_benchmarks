#!/bin/bash

set -e

mkdir -p figures

./scripts/plot_validation_difference.py "$(cd hyrise && git rev-parse HEAD)" -s symlog
./scripts/plot_validation_time.py "$(cd hyrise && git rev-parse HEAD)" -s symlog
./scripts/plot_performance_impact.py "$(cd hyrise && git rev-parse HEAD)" -s symlog
./scripts/plot_tradeoff_sf.py "$(cd hyrise && git rev-parse HEAD)" -s symlog
./scripts/plot_comparison.py
