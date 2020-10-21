#!/bin/sh

fontforge -script ./tools/dataset_maker_ff.py --input="./input/gothic" --output="./gothic"
python3 ./tools/dataset_maker.py --input="./input/gothic" --output="./gothic"
