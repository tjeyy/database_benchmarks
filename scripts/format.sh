#!/bin/bash

isort --trailing-comma --line-width 120 --multi-line 3 -q python

black --line-length 120 python -q
