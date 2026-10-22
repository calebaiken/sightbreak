#!/usr/bin/env python3
"""Inspect pinned template object symbols; does not inspect the final linked app."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

parser = argparse.ArgumentParser()
parser.add_argument('archive', type=Path)
args = parser.parse_args()
member = 'metal_cpp.ios.template_debug.arm64.o'
objects = []
with args.archive.open('rb') as stream:
    assert stream.read(8) == b'!<arch>\n'
    while header := stream.read(60):
        assert len(header) == 60 and header[58:] == b'`\n'
        size = int(header[48:58]); name = header[:16].decode().strip(); data = stream.read(size)
        assert len(data) == size
        if size % 2:
            assert stream.read(1) == b'\n'
        if name.startswith('#1/'):
            count = int(name[3:]); name = data[:count].rstrip(b'\0').decode(); data = data[count:]
        else:
            name = name.rstrip('/')
        if name == member:
            objects.append(data)
assert len(objects) == 1
data = objects[0]
magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack_from('<8I', data)
assert magic == 0xFEEDFACF and cpu == 0x0100000C and kind == 1
offset = 32; versions = []; symbols = None
version = lambda value: f'{value >> 16}.{(value >> 8) & 255}.{value & 255}'
for _ in range(count):
    command, length = struct.unpack_from('<II', data, offset)
    assert length >= 8
    if command == 2:
        symbols = struct.unpack_from('<6I', data, offset)[2:]
    if command == 0x32:
        platform, minimum, sdk, tools = struct.unpack_from('<4I', data, offset + 8)
        versions.append({'platform': platform, 'minimum_os': version(minimum), 'sdk': version(sdk)})
    offset += length
assert offset == 32 + size and symbols is not None
symoff, nsyms, stroff, strsize = symbols; strings = data[stroff:stroff + strsize]
wanted = {'_CADynamicRangeAutomatic', '_CADynamicRangeConstrainedHigh', '_CADynamicRangeHigh', '_CADynamicRangeStandard', '_MTLTensorDomain'}
records = []
for index in range(nsyms):
    start, n_type, section, description, value = struct.unpack_from('<IBBHQ', data, symoff + index * 16)
    name = strings[start:strings.find(b'\0', start)].decode()
    if name in wanted:
        records.append({'symbol': name, 'type': n_type, 'section': section, 'description': description,
                        'weak_reference': bool(description & 0x40), 'undefined_external': bool(n_type & 1) and n_type & 0xEE == 0, 'value': value})
assert len(records) == 5 and all(item['weak_reference'] and item['undefined_external'] for item in records)
with args.archive.open('rb') as stream:
    archive_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
print(json.dumps({'archive_sha256': archive_hash, 'member': member, 'member_bytes': len(data),
                  'object_sha256': hashlib.sha256(data).hexdigest(), 'build_versions': versions,
                  'required_symbol_records': records, 'scope': 'Template object only; no final-app import or runtime proof'}, indent=2))
