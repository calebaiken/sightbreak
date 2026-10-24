#!/usr/bin/env python3
"""Pure known-format/missing-evidence controls; no engine or native import."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

REPORT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('offline_diagnostic_decoder',REPORT/'analyze_actual.py')
decoder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)

class NormalResourceDecoderControls(unittest.TestCase):
    def parsed(self,text):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'reopened.log').write_bytes(text if isinstance(text,bytes) else text.encode())
            return decoder.logs(root)[0]

    def test_known_engine_formats_and_large_id(self):
        row=self.parsed('WARNING: 3 ObjectDB instances were leaked at exit (run with `--verbose` for details).\nLeaked instance: GDScript:9223372036854775851 - Reference count: 1\nLeaked instance: Node:1268224 - Node path: /root/Main\nLeaked instance: Resource:9223372036854775852 - Reference count: 2\nERROR: 1 resources still in use at exit.\nResource still in use: res://a(b).tres (Resource)\n')
        self.assertTrue(row['strict_failed'])
        self.assertTrue(row['single_summary_count_matches_rows'])
        self.assertEqual(row['instances'][0]['instance_id'],'9223372036854775851')
        self.assertEqual(row['instances'][0]['reference_count'],1)
        self.assertEqual(row['instances'][1]['node_path'],'/root/Main')
        self.assertEqual(row['separate_resource_cache_rows'][0]['path'],'res://a(b).tres')

    def test_unmatched_instance_line_preserved(self):
        row=self.parsed('Leaked instance: incomplete\n')
        self.assertEqual(len(row['unmatched_instance_lines']),1)
        self.assertTrue(row['strict_failed'])

    def test_count_difference_duplicate_and_unknown_detail_preserved(self):
        row=self.parsed('WARNING: 3 ObjectDB instances were leaked at exit.\nLeaked instance: Node:42 - Node path: \nLeaked instance: Node:42 - Other detail\n')
        self.assertFalse(row['single_summary_count_matches_rows'])
        self.assertEqual(row['instance_id_duplicates'],['42'])
        self.assertEqual(row['instances'][0]['node_path'],'')
        self.assertEqual(row['instances'][1]['parse_status'],'UNPARSED_DETAIL')

    def test_invalid_uint64_identity_retained(self):
        for value in ('0','18446744073709551616'):
            row=self.parsed('Leaked instance: Resource:'+value+' - Reference count: 1\n')
            self.assertFalse(row['instances'][0]['instance_id_in_uint64_range'])
            self.assertEqual(row['instances'][0]['instance_id'],value)

    def test_decode_replacement_visible(self):
        self.assertTrue(self.parsed(b'bad \xff text\n')['utf8_replacement_present'])

    def test_earlier_flow_and_missing_logs_write_incomplete_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            raw=root/'raw'; (raw/'offline-input').mkdir(parents=True)
            (raw/'offline-input'/'results.json').write_text('{}')
            (raw/'offline-input'/'commands.json').write_text('[]')
            with contextlib.redirect_stdout(io.StringIO()):
                decoder.review(raw,root/'out')
            report=json.loads((root/'out'/'ACTUAL_ANALYSIS.json').read_text())
            self.assertFalse(report['leak_reproduced'])
            self.assertEqual(report['diagnostic_result'],'PENDING_MANUAL_ADMISSION_AND_FLOW_REVIEW')
            self.assertIn('one reopened log available',report['evidence_checks_failed'])
            self.assertTrue(report['read_errors'])

if __name__=='__main__':
    unittest.main(verbosity=2)
