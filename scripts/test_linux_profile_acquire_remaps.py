#!/usr/bin/env python3
"""Observed R2 import bytes, original-reader falsifier and authenticated controls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import linux_profile_payload as pack
from test_linux_profile_acquire import descriptor, make_payload, manual_stage

FIXTURES = Path(__file__).resolve().parents[1] / (
    'docs/reports/gauntlet/m1-linux-profile-acquisition/packed-remap-boundary-r1/fixtures')
PACKED = FIXTURES / 'packed-assets-icon.svg.import'
STAGED = FIXTURES / 'staged-assets-icon.svg.import'
READER = FIXTURES / 'reader-216d39a.py'


def original_reader():
    spec = importlib.util.spec_from_file_location('retained_r2_payload_reader', READER)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    return reader


def observed_import_stage(root):
    """Use actual import metadata in a valid-MD5 synthetic pack, never native."""
    stage, record, resources, template, executable = manual_stage(root)
    record['files'].pop('assets/a.png.import')
    resources.pop('assets/a.png.import')
    cache = resources.pop('.godot/imported/a.ctex')
    staged, packed = STAGED.read_bytes(), PACKED.read_bytes()
    target = original_reader().sections(staged.decode())['remap']['path'][6:]
    resources.update({'assets/icon.svg.import': packed, target: cache,
                      'assets/icon.svg': b'synthetic source icon'})
    for name, raw in {'assets/icon.svg.import': staged,
                      'assets/icon.svg': resources['assets/icon.svg']}.items():
        (stage / name).write_bytes(raw)
        record['files'][name] = descriptor(raw)
    (stage / target).write_bytes(cache)
    executable.write_bytes(make_payload(template.read_bytes(), resources))
    return stage, record, resources, template, executable


class PackedRemapTests(unittest.TestCase):
    def test_observed_fixtures_and_original_reader_are_byte_pinned(self):
        for path, count, expected in (
                (PACKED, 193, 'e8717d3311cb7cd3fb716324b219d948e6f7d68fbae1b33d9163add59b4c2203'),
                (STAGED, 1020, '9b48fb27282e20a5408a15c911b83134130c1fa359d172c35d02d46a7690d76f'),
                (READER, 17270, 'bbba56a05f860d617889dec4f65a9256e6f003f7220316a6708a5009d2d152b3')):
            with self.subTest(path=path.name):
                raw = path.read_bytes()
                self.assertEqual(len(raw), count)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)

    def test_original_reader_retains_exact_actual_failure_and_staged_positive(self):
        reader = original_reader()
        self.assertEqual(set(reader.sections(STAGED.read_text())), {'remap', 'deps', 'params'})
        with self.assertRaises(json.JSONDecodeError) as observed:
            reader.sections(PACKED.read_bytes().decode())
        self.assertEqual(str(observed.exception), 'Extra data: line 4 column 1 (char 26)')

    def test_actual_packed_representation_equals_staged_remap(self):
        self.assertEqual(pack.packed_import_sections(PACKED.read_bytes()),
                         {'remap': pack.sections(STAGED.read_text())['remap']})
        with self.assertRaisesRegex(pack.Invalid, 'control'):
            pack.sections(PACKED.read_bytes().decode())
        with self.assertRaisesRegex(pack.Invalid, 'control'):
            pack.sections(STAGED.read_text() + '\0')

    def test_actual_import_metadata_passes_full_inspector_after_md5(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage, record, resources, template, executable = observed_import_stage(Path(temporary))
            result, _ = pack.inspect(executable, template, stage, record)
            retained = next(row for row in result['resources'] if row['path'] == 'assets/icon.svg.import')
            self.assertEqual(retained['sha256'], descriptor(PACKED.read_bytes())['sha256'])
            self.assertEqual(retained['md5'], hashlib.md5(PACKED.read_bytes()).hexdigest())
            self.assertEqual(result['imported_resources'][0]['source'], 'assets/icon.svg')
            with self.assertRaisesRegex(json.JSONDecodeError, 'Extra data'):
                original_reader().inspect(executable, template, stage, record)

    def test_rebuilt_md5_valid_actual_remap_boundary_and_value_mutations_reject(self):
        actual = PACKED.read_bytes()
        text = actual[:-1]
        mutations = {
            'missing NUL': text,
            'repeated NUL': actual + b'\0',
            'embedded NUL': actual.replace(b'texture', b'tex\0ture'),
            'NUL before final LF': text[:-1] + b'\0\n',
            'NUL then extra LF': actual + b'\n',
            'no terminal LF': text[:-1] + b'\0',
            'CRLF terminal': text[:-1] + b'\r\n\0',
            'trailing object': text + b'{}\n\0',
            'trailing scalar': text + b'false\n\0',
            'malformed object': actual.replace(b'false', b'false,'),
            'duplicate metadata key': actual.replace(b'false', b'false,\n"vram_texture": false'),
            'nonfinite metadata': actual.replace(b'false', b'NaN'),
            'wrong remap': actual.replace(b'icon.svg-', b'other.svg-'),
            'additional section': text + b'[params]\nanything=false\n\0',
            'duplicate section': text + b'[remap]\n\0',
            'duplicate assignment': text + b'importer="texture"\n\0',
            'invalid UTF8': actual.replace(b'texture', b'tex\xffture'),
            'escaped control': actual.replace(b'texture', b'tex\\u0000ture'),
        }
        for control in (*range(32), *range(127, 160)):
            if control != 10:
                mutations['comment control ' + str(control)] = text + b';comment' + chr(control).encode() + b'\n\0'
        for name, raw in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                stage, record, resources, template, executable = observed_import_stage(Path(temporary))
                resources['assets/icon.svg.import'] = raw
                executable.write_bytes(make_payload(template.read_bytes(), resources))
                with self.assertRaises((pack.Invalid, UnicodeError, json.JSONDecodeError)):
                    pack.inspect(executable, template, stage, record)

    def test_unauthenticated_actual_import_mutation_rejects_before_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage, record, resources, template, executable = observed_import_stage(Path(temporary))
            raw = executable.read_bytes()
            self.assertEqual(raw.count(PACKED.read_bytes()), 1)
            executable.write_bytes(raw.replace(PACKED.read_bytes(), PACKED.read_bytes()[:-1] + b'!'))
            with self.assertRaisesRegex(pack.Invalid, 'MD5 mismatch: assets/icon.svg.import'):
                pack.inspect(executable, template, stage, record)

    def test_frozen_stage_hash_precedes_staged_control_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage, record, resources, template, executable = observed_import_stage(Path(temporary))
            (stage / 'assets/icon.svg.import').write_bytes(STAGED.read_bytes() + b'\0')
            with self.assertRaisesRegex(pack.Invalid, 'frozen inventory'):
                pack.inspect(executable, template, stage, record)
            record['files']['assets/icon.svg.import'] = descriptor(STAGED.read_bytes() + b'\0')
            with self.assertRaisesRegex(pack.Invalid, 'control'):
                pack.inspect(executable, template, stage, record)


if __name__ == '__main__':
    unittest.main()
