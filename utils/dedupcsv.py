#!/usr/bin/env python3

import os
import sys

import pandas as pd

# Generate id column and drop duplicate rows.
df = pd.read_csv(sys.argv[1], dtype='object')
df.index.name = 'id'
df.drop_duplicates(inplace=True)
df.to_csv(os.path.splitext(sys.argv[1])[0] + '-dedup.csv')
