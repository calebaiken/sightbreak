#!/usr/bin/env python3
"""Exhaustive tiny InputStream oracle for relational receipt constraints."""
from itertools import combinations, product
import unittest

from analyze_input_consumption import ReceiptHistory
from test_input_consumption_observation import control
from test_input_consumption_stream import packet


class ReceiptConstraintOracle(unittest.TestCase):
    def test_receipts_match_exhaustive_staging_and_sorted_pop_ground_truth(self):
        # Ground truth follows InputStream staging (last duplicate wins) and
        # sorted pop. The candidate receives only header/count projections.
        oracle = {}
        commands = tuple(product((1,2,3), (False,True)))
        for count in (1,2,3):
            for incoming in product(commands, repeat=count):
                staged = {}
                for sequence, fire in incoming:
                    staged[sequence] = fire
                header = (count, incoming[0][0], incoming[-1][0],
                          sum(fire for _,fire in incoming), len(staged))
                oracle.setdefault(header, set()).add(tuple(sorted(staged.items())))
        checked = 0
        for (count, first, last, fire_sum, size), possible in oracle.items():
            projection = packet(0, first, last, count, fire_sum)
            for keys in combinations((1,2,3), size):
                for flags in product((False,True), repeat=size):
                    candidate = tuple(zip(keys,flags))
                    histories = [ReceiptHistory.accept(ReceiptHistory.empty(), projection, size, -1)]
                    histories = [h for h in histories if ReceiptHistory.feasible(h,size,-1)]
                    for index, (sequence,fire) in enumerate(candidate,1):
                        histories = [variant for h in histories for variant in ReceiptHistory.pop(h,control(sequence,fire))]
                        histories = [h for h in histories if ReceiptHistory.feasible(h,size-index,sequence)]
                    self.assertEqual(bool(histories), candidate in possible, (projection, candidate))
                    checked += 1
        self.assertGreater(checked, 500)

    def test_two_receipts_keep_first_queued_payload_despite_later_duplicates(self):
        commands = tuple(product((1,2), (False,True)))
        batches = [incoming for count in (1,2) for incoming in product(commands,repeat=count)]
        oracle = {}
        for first in batches:
            initial = dict(first)
            for second in batches:
                queued = dict(initial)
                for sequence,fire in dict(second).items():
                    queued.setdefault(sequence,fire)
                def header(incoming, added):
                    return (len(incoming),incoming[0][0],incoming[-1][0],sum(fire for _,fire in incoming),added)
                key = header(first,len(initial)), header(second,len(queued)-len(initial))
                oracle.setdefault(key,set()).add(tuple(sorted(queued.items())))
        checked = 0
        for (first,second), possible in oracle.items():
            size = first[-1] + second[-1]
            for keys in combinations((1,2),size):
                for flags in product((False,True),repeat=size):
                    candidate = tuple(zip(keys,flags))
                    histories = [ReceiptHistory.empty()]
                    queued = 0
                    for count,begin,end,fire_sum,added in (first,second):
                        projection = packet(0,begin,end,count,fire_sum)
                        histories = [ReceiptHistory.accept(h,projection,added,-1) for h in histories]
                        queued += added
                        histories = [h for h in histories if ReceiptHistory.feasible(h,queued,-1)]
                    for index,(sequence,fire) in enumerate(candidate,1):
                        histories = [variant for h in histories for variant in ReceiptHistory.pop(h,control(sequence,fire))]
                        histories = [h for h in histories if ReceiptHistory.feasible(h,size-index,sequence)]
                    self.assertEqual(bool(histories),candidate in possible,(first,second,candidate))
                    checked += 1
        self.assertGreater(checked, 200)


if __name__ == '__main__':
    unittest.main()
