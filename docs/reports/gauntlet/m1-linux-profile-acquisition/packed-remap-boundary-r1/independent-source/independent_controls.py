#!/usr/bin/env python3
"""Independent CPU-only controls. No native process launch is permitted."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[6])
parser.add_argument('--result', type=Path, required=True)
args = parser.parse_args()
sys.path.insert(0, str(args.root.resolve() / 'scripts'))
pack = importlib.import_module('linux_profile_payload')
data = importlib.import_module('test_linux_profile_acquire')
observed = importlib.import_module('test_linux_profile_acquire_remaps')
ROWS = []
EXCEPTIONS = (pack.Invalid, UnicodeError, json.JSONDecodeError)


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as temporary:
        yield observed.observed_import_stage(Path(temporary))


def descriptor(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def rebuild(executable, template, resources):
    executable.write_bytes(data.make_payload(template.read_bytes(), resources))
    authenticated, receipt, _ = pack.unpack_payload(executable, template)
    assert authenticated == resources
    return receipt


class IndependentControls(unittest.TestCase):
    def reject(self, label, stage, record, resources, template, executable, message=None):
        receipt = rebuild(executable, template, resources)
        try:
            pack.inspect(executable, template, stage, record)
        except EXCEPTIONS as exc:
            if message:
                self.assertIn(message, str(exc))
            ROWS.append({'case': label, 'all_resource_MD5s_verified': True,
                         'ELF_sha256': receipt['ELF_sha256'], 'rejected': True,
                         'error_type': type(exc).__name__, 'error': str(exc)})
        else:
            self.fail('Accepted adversarial case: ' + label)

    def test_original_exact_failure_and_positive(self):
        packed, staged = observed.PACKED.read_bytes(), observed.STAGED.read_bytes()
        self.assertEqual(descriptor(packed), {'bytes': 193, 'sha256':
            'e8717d3311cb7cd3fb716324b219d948e6f7d68fbae1b33d9163add59b4c2203'})
        self.assertEqual(descriptor(staged), {'bytes': 1020, 'sha256':
            '9b48fb27282e20a5408a15c911b83134130c1fa359d172c35d02d46a7690d76f'})
        self.assertEqual(descriptor(observed.READER.read_bytes()), {'bytes': 17270,
            'sha256': 'bbba56a05f860d617889dec4f65a9256e6f003f7220316a6708a5009d2d152b3'})
        old = observed.original_reader()
        with self.assertRaises(json.JSONDecodeError) as error:
            old.sections(packed.decode('utf-8'))
        self.assertEqual(str(error.exception), 'Extra data: line 4 column 1 (char 26)')
        expected = old.sections(staged.decode('utf-8'))['remap']
        self.assertEqual(pack.packed_import_sections(packed), {'remap': expected})
        with fixture() as (stage, record, resources, template, executable):
            rebuild(executable, template, resources)
            receipt, _ = pack.inspect(executable, template, stage, record)
            with self.assertRaises(json.JSONDecodeError):
                old.inspect(executable, template, stage, record)
        ROWS.append({'case': 'actual failing bytes in synthetic valid pack',
                     'original_error': str(error.exception), 'candidate_passed': True,
                     'resources': len(receipt['resources']), 'native': False})

    def test_independent_rebuilt_remap_grammar_attacks(self):
        raw = observed.PACKED.read_bytes()
        text = raw[:-1]
        mutations = {
            'BOM prefix': b'\xef\xbb\xbf' + raw,
            'leading NUL': b'\0' + raw,
            'one NUL but missing LF': text[:-1] + b'\0',
            'trailing space after NUL': raw + b' ',
            'two spaced NULs': text + b'\0 \0',
            'overlong UTF8 NUL': raw.replace(b'texture', b'tex\xc0\x80ture'),
            'UTF8 surrogate': raw.replace(b'texture', b'tex\xed\xa0\x80ture'),
            'UTF8 out of range': raw.replace(b'texture', b'tex\xf4\x90\x80\x80ture'),
            'escaped duplicate metadata key': raw.replace(b'false', b'false,\n"\\u0076ram_texture": false'),
            'metadata number overflow': raw.replace(b'false', b'1e9999'),
            'negative infinity': raw.replace(b'false', b'-Infinity'),
            'metadata JSON trailing array': raw[:-2] + b'[]\n\0',
            'metadata JSON trailing null': raw[:-2] + b'null\n\0',
            'semicolon after JSON': raw[:-2] + b'; tail\n\0',
            'metadata extra close brace': raw[:-2] + b'}\n\0',
            'metadata wrong false case': raw.replace(b'false', b'False'),
            'metadata unquoted key': raw.replace(b'"vram_texture"', b'vram_texture'),
            'escaped control key': raw.replace(b'"vram_texture"', b'"vram_texture\\u0000"'),
            'escaped section delimiter': text + b'[remap]extra\n\0',
            'assignment before section': b'extra=false\n' + raw,
            'duplicate assignment identical': text + b'importer="texture"\n\0',
        }
        for code in (1, 9, 11, 12, 13, 31, 127, 128, 133, 159):
            mutations['raw control before section ' + str(code)] = chr(code).encode('utf-8') + raw
        for label, mutated in mutations.items():
            with self.subTest(label=label), fixture() as values:
                stage, record, resources, template, executable = values
                resources['assets/icon.svg.import'] = mutated
                self.reject(label, *values, message=None)

    def test_staged_same_byte_hash_and_no_second_text_read(self):
        with fixture() as values:
            stage, record, resources, template, executable = values
            target = stage / 'assets/icon.svg.import'
            original_read = Path.read_bytes
            reads = []
            def read(path):
                raw = original_read(path)
                if path == target:
                    reads.append(raw)
                    path.write_bytes(b'changed after authenticated first staged read\n')
                return raw
            with patch.object(Path, 'read_bytes', read), patch.object(Path, 'read_text', autospec=True,
                    side_effect=lambda path, *a, **k: original_read(path).decode('utf-8')
                    if path != target else self.fail('Separate staged import semantic read')):
                pack.inspect(executable, template, stage, record)
            self.assertEqual(reads, [observed.STAGED.read_bytes()])
            ROWS.append({'case': 'staged semantic parse uses frozen first byte read',
                         'import_byte_reads': len(reads), 'passed': True,
                         'scope': 'No filesystem immutability claim after this read'})

    def test_rehashed_staged_raw_controls_and_duplicates(self):
        staged = observed.STAGED.read_bytes()
        mutations = {
            'staged terminal NUL': staged + b'\0',
            'staged invalid UTF8': staged.replace(b'texture', b'tex\xffture'),
            'staged raw tab comment': staged + b';bad\tcomment\n',
            'staged duplicate deps': staged + b'[deps]\n',
            'staged duplicate params': staged + b'[params]\n',
            'staged escaped duplicate metadata': staged.replace(b'false', b'false,\n"\\u0076ram_texture": false'),
        }
        for label, mutated in mutations.items():
            with self.subTest(label=label), fixture() as values:
                stage, record, resources, template, executable = values
                (stage / 'assets/icon.svg.import').write_bytes(mutated)
                record['files']['assets/icon.svg.import'] = descriptor(mutated)
                self.reject(label, *values)

    def test_packed_and_staged_matching_unsafe_paths_reject(self):
        for target in ('.godot/imported/../outside.ctex', '.godot/imported/./a.ctex',
                       '.godot/imported//a.ctex', '.godot/imported/tests/a.ctex',
                       '.godot/imported/back\\slash.ctex'):
            with self.subTest(target=target), fixture() as values:
                stage, record, resources, template, executable = values
                old = pack.sections(observed.STAGED.read_text())['remap']['path']
                new = 'res://' + target
                # JSON encoding retains literal path characters correctly.
                old_value, new_value = json.dumps(old).encode(), json.dumps(new).encode()
                staged = observed.STAGED.read_bytes().replace(old_value, new_value)
                resources['assets/icon.svg.import'] = observed.PACKED.read_bytes().replace(old_value, new_value)
                self.assertNotEqual(staged, observed.STAGED.read_bytes())
                (stage / 'assets/icon.svg.import').write_bytes(staged)
                record['files']['assets/icon.svg.import'] = descriptor(staged)
                self.reject('matching unsafe target ' + target, *values, message='Unsafe/test pack path')

    def test_unexpected_resources_and_changed_cache(self):
        for mode in ('extra-import', 'extra-text', 'changed-cache'):
            with self.subTest(mode=mode), fixture() as values:
                stage, record, resources, template, executable = values
                if mode == 'extra-import':
                    resources['assets/unbound.import'] = observed.PACKED.read_bytes()
                elif mode == 'extra-text':
                    resources['unbound.txt'] = b'not declared'
                else:
                    target = pack.packed_import_sections(observed.PACKED.read_bytes())['remap']['path'][6:]
                    resources[target] = b'changed cache with valid MD5'
                self.reject(mode, *values)

    def test_remap_boundary_cannot_run_before_resource_MD5(self):
        with fixture() as values:
            stage, record, resources, template, executable = values
            raw = executable.read_bytes()
            self.assertEqual(raw.count(observed.PACKED.read_bytes()), 1)
            executable.write_bytes(raw.replace(observed.PACKED.read_bytes(),
                observed.PACKED.read_bytes().replace(b'false', b'true ')))
            with patch.object(pack, 'packed_import_sections', side_effect=self.fail):
                with self.assertRaisesRegex(pack.Invalid, 'MD5 mismatch: assets/icon.svg.import'):
                    pack.inspect(executable, template, stage, record)
            ROWS.append({'case': 'MD5 rejection precedes any packed remap parse',
                         'rejected': True, 'parser_calls': 0})

    def test_nested_duplicate_keys_cannot_hide_behind_semantic_equality(self):
        for escaped in (False, True):
            with self.subTest(escaped=escaped), fixture() as values:
                stage, record, resources, template, executable = values
                # A single nested value in staged source has the same decoded
                # value as both duplicate packed forms under normal json.loads.
                staged_value = b'false,\n"nested": {"v": 0}'
                duplicate = b'false,\n"nested": {"v": 0, "' + (
                    b'\\u0076' if escaped else b'v') + b'": 0}'
                staged = observed.STAGED.read_bytes().replace(b'false', staged_value, 1)
                (stage / 'assets/icon.svg.import').write_bytes(staged)
                record['files']['assets/icon.svg.import'] = descriptor(staged)
                resources['assets/icon.svg.import'] = observed.PACKED.read_bytes().replace(b'false', duplicate)
                self.reject('nested duplicate key escaped=' + str(escaped), *values,
                            message='Duplicate import JSON key')

    def test_ecfg_and_ledger_attacks_survive_MD5_then_reject(self):
        for mode in ('ECFG-tail', 'ECFG-count', 'ECFG-boolean-type', 'ECFG-selector', 'ledger-source'):
            with self.subTest(mode=mode), fixture() as values:
                stage, record, resources, template, executable = values
                if mode == 'ECFG-tail':
                    resources['project.binary'] += b'\0'
                elif mode == 'ECFG-count':
                    value = bytearray(resources['project.binary']); struct.pack_into('<I', value, 4, 10000)
                    resources['project.binary'] = bytes(value)
                elif mode == 'ECFG-boolean-type':
                    resources['project.binary'] = data.project_binary({'debug/settings/stdout/print_gpu_profile': 0})
                elif mode == 'ECFG-selector':
                    resources['project.binary'] = data.project_binary({'display/window/size/viewport_width.linux': 1280})
                else:
                    ledger = json.loads(resources['diagnostics/source_ledger.json'])
                    ledger['source']['fixture_sha256'] = '0' * 64
                    resources['diagnostics/source_ledger.json'] = json.dumps(ledger).encode()
                self.reject(mode, *values)

    def test_pack_path_size_and_binary_bounds(self):
        # All resources keep valid MD5. Only directory/header structure changes.
        for mode in ('traversal-path', 'absolute-path', 'test-path', 'oversize-path', 'zero-path-size',
                     'duplicate-path', 'resource-size-overrun', 'resource-overlap', 'directory-tail',
                     'template-byte', 'trailer-length'):
            with self.subTest(mode=mode), fixture() as values:
                stage, record, resources, template, executable = values
                if mode in ('traversal-path', 'absolute-path', 'test-path', 'oversize-path'):
                    name = {'traversal-path':'../evil', 'absolute-path':'/evil', 'test-path':'tests/evil',
                            'oversize-path':'x' * 16385}[mode]
                    resources[name] = b'payload'
                raw = bytearray(data.make_payload(template.read_bytes(), resources))
                start = len(template.read_bytes())
                directory = start + struct.unpack_from('<Q', raw, start + 32)[0]
                first = directory + 4
                size = struct.unpack_from('<I', raw, first)[0]
                entry = first + 4 + size
                second = entry + 36
                if mode == 'zero-path-size': struct.pack_into('<I', raw, first, 0)
                elif mode == 'duplicate-path':
                    second_size = struct.unpack_from('<I', raw, second)[0]
                    # Rebuild a duplicate directory row without changing data.
                    count = struct.unpack_from('<I', raw, directory)[0]
                    first_row = raw[first:second]
                    tail_end = len(raw)-12
                    raw[tail_end:tail_end] = first_row
                    struct.pack_into('<I', raw, directory, count+1)
                    struct.pack_into('<Q', raw, len(raw)-12, len(raw)-12-start)
                    struct.pack_into('<Q', raw, 256+32, len(raw)-start)
                elif mode == 'resource-size-overrun': struct.pack_into('<Q', raw, entry+8, len(raw)*2)
                elif mode == 'resource-overlap':
                    second_size = struct.unpack_from('<I', raw, second)[0]
                    second_entry = second+4+second_size
                    # Point the second row at the first payload and match its size/hash.
                    raw[second_entry:second_entry+32] = raw[entry:entry+32]
                elif mode == 'directory-tail':
                    raw[-12:-12] = b'X'
                    struct.pack_into('<Q', raw, len(raw)-12, len(raw)-12-start)
                    struct.pack_into('<Q', raw, 256+32, len(raw)-start)
                elif mode == 'template-byte': raw[17] ^= 1
                elif mode == 'trailer-length': struct.pack_into('<Q', raw, len(raw)-12, 0)
                executable.write_bytes(raw)
                with self.assertRaises(EXCEPTIONS) as caught:
                    pack.unpack_payload(executable, template)
                ROWS.append({'case': mode, 'rejected': True, 'error': str(caught.exception),
                             'resource_hashes_rebuilt_before_structure_mutation': True})


if __name__ == '__main__':
    # Any accidental production process launch from these pure controls fails.
    with patch('subprocess.Popen', side_effect=AssertionError('Pure source review only')):
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(IndependentControls)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    args.result.write_text(json.dumps({'root': str(args.root.resolve()), 'tests_run': result.testsRun,
        'passed': result.wasSuccessful(), 'rows': ROWS}, indent=2) + '\n')
    sys.exit(0 if result.wasSuccessful() else 1)
