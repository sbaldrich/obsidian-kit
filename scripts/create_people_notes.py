"""
This script takes in csv data from stdin and converts it into multiple
notes using the 'People' template.
The csv columns are as follows:

name, alias, birth_date, relation

NOTE: Existing notes won't be overwritten.
"""
import pandas as pd
import sys
import os
from datetime import date

df = pd.read_csv(sys.stdin)
today = date.today().isoformat()
for name, alias, birth_date, relation in df.itertuples(index=False):
    if not os.path.exists(f'{name}.md'):
        with open(f'{name}.md', 'w') as of:
            lines = [
                '---',
                'category: "[[People]]"',
                f'start: {today}',
                f'last: {today}',
                f'name: {name}',
                f'alias: {alias}',
                f'birth_date: {birth_date}',
                f'relation: {relation}',
                '---'
            ]
            of.write('\n'.join(lines))
