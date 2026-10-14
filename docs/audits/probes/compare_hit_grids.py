"""Compare hit_grid_probe.gd outputs cell by cell: where a build scores hits that the
0.3.0 baseline did not, and where it stopped scoring them.

Usage: python3 compare_hit_grids.py baseline.json other.json [label]
"""
import json
import sys
from collections import Counter


def load(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def main():
    base, other = load(sys.argv[1]), load(sys.argv[2])
    label = sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]
    print(f'# {label} vs 0.3.0 baseline ({other["build"]} vs {base["build"]})')
    print('| View | Baseline H/B/miss | Build H/B/miss | New hits (miss→hit) | Lost hits (hit→miss) | H→B | B→H | New-hit rows (cm above feet) |')
    print('| --- | --- | --- | ---: | ---: | ---: | ---: | --- |')
    totals = Counter()
    for view, data in base['views'].items():
        rows_a, rows_b = data['rows'], other['views'][view]['rows']
        y0 = data['y_cm'][0]
        changes = Counter()
        new_rows = []
        for index, (row_a, row_b) in enumerate(zip(rows_a, rows_b)):
            row_new = 0
            for a, b in zip(row_a, row_b):
                if a == b:
                    continue
                changes[a + b] += 1
                if a == '.':
                    row_new += 1
            if row_new:
                new_rows.append(index + y0)
        new = changes['.B'] + changes['.H']
        lost = changes['B.'] + changes['H.']
        totals.update({'new': new, 'lost': lost, 'HB': changes['HB'], 'BH': changes['BH']})
        span = f'{min(new_rows):g}–{max(new_rows):g}' if new_rows else '—'
        ca, cb = base['counts'][view], other['counts'][view]
        print(f'| {view} | {ca["H"]}/{ca["B"]}/{ca["."]} | {cb["H"]}/{cb["B"]}/{cb["."]} | {new} | {lost} | {changes["HB"]} | {changes["BH"]} | {span} |')
    print(f'\nTotals: new hits {totals["new"]}, lost hits {totals["lost"]}, headshot→body {totals["HB"]}, body→headshot {totals["BH"]}')


if __name__ == '__main__':
    main()
