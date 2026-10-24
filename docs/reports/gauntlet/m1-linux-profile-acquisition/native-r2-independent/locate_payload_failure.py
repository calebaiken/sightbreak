#!/usr/bin/env python3
"""Independent read-only reconstruction of the actual artifact failure input."""
import hashlib
import json
from pathlib import Path
import re
import struct

RAW = Path('/workspace/sightbreak-linux-profile-fixture-native-types/builds/linux-profile-acquisition-r2')
REPORT = Path(__file__).resolve().parent


def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def observed_failure(data):
    """Reconstruct the frozen section-value boundary without importing its code."""
    section, pending = None, []
    def flush():
        if not pending:
            return None
        key, value = '\n'.join(pending).split('=', 1)
        pending.clear()
        try:
            json.loads(value)
        except json.JSONDecodeError as error:
            return {'section': section, 'key': key, 'value_repr': repr(value),
                    'error': str(error), 'position': error.pos,
                    'line': error.lineno, 'column': error.colno}
        return None
    for line in data.decode().splitlines():
        if not line.strip() or line.startswith(';'):
            continue
        if re.fullmatch(r'\[[a-z_]+\]', line):
            if found := flush():
                return found
            section = line[1:-1]
        elif re.match(r'^[A-Za-z_][A-Za-z_0-9/.]*=', line):
            if found := flush():
                return found
            pending.append(line)
        else:
            pending.append(line)
    return flush()


def main():
    executable = RAW / 'export/linux-profile-diagnostic.x86_64'
    data = executable.read_bytes()
    length, trailer_magic = struct.unpack('<QI', data[-12:])
    assert trailer_magic == 0x43504447
    start = len(data) - 12 - length
    pack = data[start:-12]
    header = struct.unpack_from('<6I2Q', pack)
    assert header[:6] == (0x43504447, 4, 4, 7, 2, 2)
    position = header[7]
    count, = struct.unpack_from('<I', pack, position)
    position += 4
    resources, table = {}, []
    for _ in range(count):
        size, = struct.unpack_from('<I', pack, position)
        position += 4
        name = pack[position:position + size].rstrip(b'\0').decode()
        position += size
        offset, amount, md5, flags = struct.unpack_from('<QQ16sI', pack, position)
        position += 36
        begin, end = header[6] + offset, header[6] + offset + amount
        assert 104 <= begin < end <= header[7] and name not in resources and flags == 0
        content = pack[begin:end]
        assert hashlib.md5(content).digest() == md5
        resources[name] = content
        table.append({'path': name, 'pack_offset': begin, 'md5': md5.hex(), **identity(content)})
    stage_record = json.loads((RAW / 'diagnostic-stage.json').read_bytes())
    failure = None
    staged_imports = 0
    for name in stage_record['files']:
        if not name.endswith('.import'):
            continue
        original = (RAW / 'project' / name).read_bytes()
        assert observed_failure(original) is None
        staged_imports += 1
        packed = resources[name]
        found = observed_failure(packed)
        if found:
            failure = {'resource': name, 'stage_path': str(RAW / 'project' / name),
                       'staged_identity': identity(original), 'packed_identity': identity(packed),
                       'packed_tail_repr': repr(packed[-36:]), 'reproduction': found}
            assert name == 'assets/icon.svg.import' and packed.endswith(b'\n}\n\0')
            assert found['error'] == 'Extra data: line 4 column 1 (char 26)'
            assert observed_failure(packed[:-1]) is None
            assert b'\0' not in original
            target = REPORT / 'failure-input'
            target.mkdir(exist_ok=True)
            (target / 'packed-assets-icon.svg.import').write_bytes(packed)
            (target / 'staged-assets-icon.svg.import').write_bytes(original)
            break
    assert failure is not None
    overall = json.loads((RAW / 'overall.json').read_bytes())
    assert overall['error'] == failure['reproduction']['error']
    assert overall['phases'][-1]['name'] == 'artifact' and overall['phases'][-1]['passed'] is False
    result = {'passed': True, 'acquisition_verdict': 'FAILED', 'failing_phase': 'artifact',
              'ELF_path': str(executable), 'ELF_identity': identity(data),
              'PCK_identity': identity(pack), 'PCK_start': start, 'PCK_header': list(header),
              'resource_count': count, 'resources': table, 'failure': failure,
              'controls': {'staged_import_before_failure_parses': staged_imports,
                           'same_packed_bytes_without_single_final_NUL_parse': True},
              'scope': 'Failure-input reconstruction only; stripping the final byte is a diagnostic control, not an approved repair or full payload acceptance.'}
    (REPORT / 'payload-failure-readback.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'resources'}, indent=2))


if __name__ == '__main__':
    main()
