#!/usr/bin/env python3
"""Actual filesystem replacement/ownership checks; no Godot or gameplay claim."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from native_observation import open_shared_text, read_observation_json


class NativeObservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.status = self.directory / 'statüs.json'
        self.replacement = self.directory / 'status.json.tmp'
        self.old = '{"generation":1,"text":"old snapshot"}'
        self.new = '{"generation":2,"text":"new snapshot"}'
        self.status.write_text(self.old, encoding='utf-8')
        self.replacement.write_text(self.new, encoding='utf-8')

    def test_open_reader_allows_atomic_replace_and_keeps_original_snapshot(self):
        with open_shared_text(self.status) as reader:
            descriptor = reader.fileno()
            os.replace(self.replacement, self.status)
            self.assertEqual(reader.read(), self.old)
            self.assertEqual(read_observation_json(self.status), json.loads(self.new))
        self.assertTrue(reader.closed)
        with self.assertRaises(OSError):
            os.fstat(descriptor)

    @unittest.skipUnless(os.name == 'nt', 'Windows CRT delete-sharing baseline requires native Windows')
    def test_ordinary_windows_reader_blocks_atomic_replace_until_closed(self):
        with self.status.open('r', encoding='utf-8') as reader:
            with self.assertRaises(PermissionError):
                os.replace(self.replacement, self.status)
            self.assertEqual(reader.read(), self.old)
            self.assertEqual(self.status.read_text(encoding='utf-8'), self.old)
        os.replace(self.replacement, self.status)
        self.assertEqual(self.status.read_text(encoding='utf-8'), self.new)

    def test_byte_limit_counts_utf8_bytes_and_rejects_oversized_snapshot(self):
        payload = json.dumps({'text': 'é雪'}, ensure_ascii=False).encode('utf-8')
        self.status.write_bytes(payload)
        self.assertEqual(read_observation_json(self.status, max_bytes=len(payload)), {'text': 'é雪'})
        with self.assertRaisesRegex(ValueError, 'bounded byte budget'):
            read_observation_json(self.status, max_bytes=len(payload) - 1)
        with self.assertRaisesRegex(ValueError, 'positive'):
            read_observation_json(self.status, max_bytes=0)
        self.status.write_bytes(b' ' * (2 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, 'bounded byte budget'):
            read_observation_json(self.status)

    def test_missing_invalid_utf8_and_malformed_json_are_not_accepted(self):
        with self.assertRaises(FileNotFoundError):
            read_observation_json(self.directory / 'missing.json')
        self.status.write_bytes(b'\xff')
        with self.assertRaises(UnicodeDecodeError):
            read_observation_json(self.status)
        self.status.write_text('{"incomplete":', encoding='utf-8')
        with self.assertRaises(json.JSONDecodeError):
            read_observation_json(self.status)

    def test_exception_inside_reader_closes_its_actual_descriptor(self):
        with self.assertRaisesRegex(RuntimeError, 'consumer stopped'):
            with open_shared_text(self.status) as reader:
                descriptor = reader.fileno()
                raise RuntimeError('consumer stopped')
        self.assertTrue(reader.closed)
        with self.assertRaises(OSError):
            os.fstat(descriptor)


if __name__ == '__main__':
    unittest.main()
