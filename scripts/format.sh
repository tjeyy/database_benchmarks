#!/bin/bash

isort --trailing-comma --line-width 120 --multi-line 3 -q python
isort --trailing-comma --line-width 120 --multi-line 3 -q scripts

black --line-length 120 python -q
black --line-length 120 scripts -q
