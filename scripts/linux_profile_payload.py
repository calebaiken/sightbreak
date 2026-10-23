#!/usr/bin/env python3
"""Pure inspection of the diagnostic text-script ELF/PCK, before any seal claim."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct

from linux_profile_overhead import Invalid, require, strict_json

MAGIC = 0x43504447
CRITICAL = {
    'application/run/main_scene': 'res://diagnostics/linux_profile_overhead.tscn',
    'display/window/size/viewport_width': 1280,
    'display/window/size/viewport_height': 720,
    'display/window/size/window_width_override': 1280,
    'display/window/size/window_height_override': 720,
    'rendering/renderer/rendering_method': 'gl_compatibility',
    'rendering/renderer/rendering_method.mobile': 'gl_compatibility',
    'rendering/anti_aliasing/quality/msaa_3d': 1,
    'rendering/driver/threads/thread_model': 1,
    'debug/settings/stdout/print_gpu_profile': False,
    'editor/export/convert_text_resources_to_binary': False,
}
# These explicit staged values equal pinned engine defaults and save_custom may
# omit them. Runtime getters/argv remain enforced by the accepted controller.
DEFAULTS = {'rendering/driver/threads/thread_model': 1,
            'debug/settings/stdout/print_gpu_profile': False}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(name):
    require(isinstance(name, str) and name and '\\' not in name and '\0' not in name
            and not name.startswith('/') and name == PurePosixPath(name).as_posix()
            and all(part not in ('', '.', '..', 'tests') for part in name.split('/')),
            'Unsafe/test pack path: ' + repr(name))
    return name


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, count):
        require(type(count) is int and count >= 0 and self.pos + count <= len(self.data), 'Truncated binary')
        value = self.data[self.pos:self.pos + count]
        self.pos += count
        return value

    def unpack(self, pattern):
        return struct.unpack(pattern, self.take(struct.calcsize(pattern)))

    def string(self, limit=1048576):
        count, = self.unpack('<I')
        require(count <= limit, 'Oversize string')
        value = self.take(count).decode('utf-8')
        require('\0' not in value, 'Embedded NUL string')
        return value

    def done(self):
        require(self.pos == len(self.data), 'Unexpected trailing binary bytes')


def scalar(data):
    reader = Reader(data)
    kind, = reader.unpack('<I')
    if kind == 1:
        value, = reader.unpack('<I')
        require(value in (0, 1), 'Invalid bool')
        value = bool(value)
    elif kind in (2, 2 | (1 << 16)):
        value, = reader.unpack('<q' if kind >> 16 else '<i')
    elif kind in (3, 3 | (1 << 16)):
        value, = reader.unpack('<d' if kind >> 16 else '<f')
    elif kind == 4:
        value = reader.string()
        require(not any(reader.take((-reader.pos) % 4)), 'Nonzero Variant string padding')
    else:
        raise Invalid('Unsupported critical Variant type')
    reader.done()
    return value


def project_properties(data):
    reader = Reader(data)
    require(reader.take(4) == b'ECFG', 'Missing ECFG project header')
    count, = reader.unpack('<I')
    require(0 < count < 10000, 'Invalid project property count')
    result = {}
    for _ in range(count):
        key = reader.string()
        require(key not in result, 'Duplicate project key')
        size, = reader.unpack('<I')
        result[key] = reader.take(size)
    reader.done()
    for key, wanted in CRITICAL.items():
        value = scalar(result[key]) if key in result else DEFAULTS.get(key)
        require(type(value) is type(wanted) and value == wanted, 'Wrong packed project setting: ' + key)
    return {key: scalar(result[key]) if key in result else DEFAULTS[key] for key in CRITICAL}


def elf_sections(data):
    require(len(data) >= 64 and data[:7] == b'\x7fELF\x02\x01\x01', 'Wrong ELF class/order/version')
    kind, machine, version = struct.unpack_from('<HHI', data, 16)
    require(kind in (2, 3) and machine == 62 and version == 1, 'Wrong ELF type/architecture')
    phoff, shoff = struct.unpack_from('<QQ', data, 32)
    ehsize, phsize, phcount, shsize, shcount, strings = struct.unpack_from('<6H', data, 52)
    require(ehsize == 64 and phsize == 56 and shsize == 64 and 0 < strings < shcount < 10000
            and phoff + phsize * phcount <= len(data) and shoff + shsize * shcount <= len(data), 'Invalid ELF tables')
    for index in range(phcount):
        segment = struct.unpack_from('<II6Q', data, phoff + index * phsize)
        require(segment[2] + segment[5] <= len(data), 'ELF segment outside file')
    string_head = shoff + strings * shsize
    string_offset, string_size = struct.unpack_from('<QQ', data, string_head + 24)
    require(string_offset + string_size <= len(data), 'Invalid ELF section strings')
    names, result = data[string_offset:string_offset + string_size], {}
    for index in range(shcount):
        at = shoff + index * shsize
        name, section_type, _flags, _address, offset, size, *_ = struct.unpack_from('<II4Q2I2Q', data, at)
        require(name < len(names), 'Invalid section name')
        end = names.find(b'\0', name)
        require(end >= name, 'Unterminated section name')
        label = names[name:end].decode()
        require(label not in result, 'Duplicate ELF section name')
        require(section_type == 8 or offset + size <= len(data), 'ELF section outside file')
        result[label] = {'header_offset': at, 'offset': offset, 'bytes': size}
    require('pck' in result, 'ELF lacks pck section')
    return result


def unpack_payload(executable, template):
    data, original = Path(executable).read_bytes(), Path(template).read_bytes()
    sections, original_sections = elf_sections(data), elf_sections(original)
    length, magic = struct.unpack('<QI', data[-12:])
    require(magic == MAGIC and 104 < length < len(data) - 12, 'Invalid embedded trailer')
    start = len(data) - 12 - length
    require(start == len(original), 'Pack does not start at the pinned template EOF')
    section = sections['pck']
    require(section['header_offset'] == original_sections['pck']['header_offset']
            and section['offset'] == start and section['bytes'] == length + 12, 'Wrong ELF pck fixup')
    prefix = bytearray(data[:start])
    at = section['header_offset'] + 24
    prefix[at:at + 16] = original[at:at + 16]
    require(prefix == original, 'Export executable differs from pinned template outside pack fixup')
    pack = data[start:-12]
    header = struct.unpack_from('<6I2Q', pack)
    require(header[:6] == (MAGIC, 4, 4, 7, 2, 2) and header[6] == 104
            and 104 <= header[7] < length and not any(pack[40:104]), 'Wrong PCK header/version/flags/reserved')
    directory = Reader(pack[header[7]:])
    count, = directory.unpack('<I')
    require(0 < count < 10000, 'Invalid pack resource count')
    resources, inventory, ranges = {}, [], []
    for _ in range(count):
        size, = directory.unpack('<I')
        require(0 < size <= 16384 and size % 4 == 0, 'Invalid padded resource path')
        name = directory.take(size)
        unpadded = name.rstrip(b'\0')
        require(name == unpadded + b'\0' * (size - len(unpadded)), 'Bad path padding')
        path = safe_path(unpadded.decode())
        offset, amount, md5, flags = directory.unpack('<QQ16sI')
        begin, end = header[6] + offset, header[6] + offset + amount
        require(path not in resources and flags == 0 and amount > 0
                and 104 <= begin < end <= header[7], 'Duplicate/empty/out-of-range/encrypted resource')
        raw = pack[begin:end]
        require(hashlib.md5(raw).digest() == md5, 'Pack resource MD5 mismatch: ' + path)
        resources[path] = raw
        ranges.append((begin, end))
        inventory.append({'path': path, 'bytes': amount, 'sha256': sha(raw), 'md5': md5.hex(),
                          'pack_offset': begin})
    require(all(left[1] <= right[0] for left, right in zip(sorted(ranges), sorted(ranges)[1:])), 'Overlapping resources')
    require(not any(directory.take(len(directory.data) - directory.pos)), 'Nonzero pack directory tail')
    return resources, {'ELF_sha256': sha(data), 'ELF_bytes': len(data), 'PCK_start': start,
                       'PCK_bytes': length, 'PCK_sha256': sha(pack), 'PCK_header': list(header),
                       'template_sha256': sha(original), 'resources': inventory}, pack


def sections(text):
    result, current, pending = {}, None, []
    def flush():
        if pending:
            key, value = '\n'.join(pending).split('=', 1)
            require(key not in result[current], 'Duplicate import key')
            result[current][key] = strict_json(value)
            pending.clear()
    for line in text.splitlines():
        if not line.strip() or line.startswith(';'):
            continue
        if re.fullmatch(r'\[[a-z_]+\]', line):
            flush()
            current = line[1:-1]
            require(current not in result, 'Duplicate import section')
            result[current] = {}
        elif re.match(r'^[A-Za-z_][A-Za-z_0-9/.]*=', line):
            flush()
            require(current is not None, 'Import assignment outside section')
            pending.append(line)
        else:
            require(pending, 'Unexpected import syntax')
            pending.append(line)
    flush()
    return result


def uid_cache(data):
    reader, result, ids = Reader(data), {}, set()
    count, = reader.unpack('<I')
    require(count < 10000, 'Invalid UID count')
    for _ in range(count):
        identity, = reader.unpack('<Q')
        path = reader.string()
        require(path.startswith('res://') and path not in result and identity not in ids, 'Duplicate/unsafe UID')
        safe_path(path[6:])
        result[path] = identity
        ids.add(identity)
    reader.done()
    return result


def classes(data):
    text = data.decode().strip()
    require(text.startswith('list='), 'Missing class cache list')
    rows = strict_json(re.sub(r'&(?=")', '', text[5:]))
    require(type(rows) is list and all(type(row) is dict for row in rows), 'Malformed class cache')
    result = {}
    for row in rows:
        path = row.get('path')
        require(isinstance(path, str) and path.startswith('res://') and path not in result, 'Duplicate class path')
        safe_path(path[6:])
        require(row.get('language') == 'GDScript' and isinstance(row.get('class'), str), 'Unexpected class language')
        result[path] = row
    return result


def inspect(executable, template, stage, record):
    stage = Path(stage)
    resources, result, pack = unpack_payload(executable, template)
    expected, imported, source_paths = set(), [], set()
    # Every frozen script and text scene/resource is directly inspected; no
    # GDC token signature or assertion in a seal substitutes for equality.
    for name in record['files']:
        path = stage / name
        original_bytes = path.read_bytes()
        require(len(original_bytes) == record['files'][name]['bytes']
                and sha(original_bytes) == record['files'][name]['sha256'], 'Staged file differs from frozen inventory: ' + name)
        if path.suffix in ('.gd', '.tscn', '.tres', '.gdshader') or name == 'diagnostics/source_ledger.json':
            require(name in resources and resources[name] == path.read_bytes(), 'Missing/changed text source: ' + name)
            expected.add(name)
            source_paths.add('res://' + name)
        if name.endswith('.import'):
            original = sections(path.read_text())
            require(set(original) == {'remap', 'deps', 'params'}, 'Unexpected staged import sections')
            require(name in resources, 'Missing packed import metadata: ' + name)
            packed = sections(resources[name].decode())
            require(set(packed) == {'remap'}, 'Unexpected packed import sections')
            wanted = {key: value for key, value in original['remap'].items()
                      if not key.startswith('path.') or key == 'path.s3tc'}
            require(packed['remap'] == wanted, 'Changed import remap: ' + name)
            original_name = name[:-7]
            require(original['deps']['source_file'] == 'res://' + original_name and original_name in record['files'],
                    'Unbound import source')
            expected.add(name)
            source_paths.add('res://' + original_name)
            for key, target in wanted.items():
                if key == 'path' or key.startswith('path.'):
                    require(target.startswith('res://.godot/imported/'), 'Unexpected import target')
                    target = safe_path(target[6:])
                    require(target in resources and resources[target] == (stage / target).read_bytes(), 'Missing/changed import cache: ' + target)
                    expected.add(target)
                    imported.append({'source': original_name, 'source_sha256': record['files'][original_name]['sha256'],
                                     'target': target, 'cache_sha256': sha(resources[target])})
    icon = 'assets/icon.svg'
    if icon in record['files']:
        require(resources.get(icon) == (stage / icon).read_bytes(), 'Changed forced icon')
        expected.add(icon)
    required = {'diagnostics/linux_profile_overhead.gd', 'diagnostics/linux_profile_overhead.tscn',
                'diagnostics/source_ledger.json'}
    require(required <= expected, 'Missing diagnostic source/scene/ledger')
    ledger = strict_json(resources['diagnostics/source_ledger.json'].decode())
    require(ledger['source'] == record['source'] and ledger['content'] == record['base_files'], 'Packed ledger provenance differs')
    require(sha(resources['diagnostics/linux_profile_overhead.gd']) == record['source']['fixture_sha256']
            and sha(resources['diagnostics/linux_profile_overhead.tscn']) == record['source']['scene_sha256'],
            'Packed fixture/scene differs from frozen source identity')
    packed_classes = classes(resources['.godot/global_script_class_cache.cfg'])
    require(packed_classes == {path: row for path, row in classes((stage / '.godot/global_script_class_cache.cfg').read_bytes()).items()
                               if path in source_paths}, 'Packed class cache differs from staged resources')
    for path, row in packed_classes.items():
        require(path[6:] in resources and re.search(r'^class_name\s+' + re.escape(row['class']) + r'\b',
                resources[path[6:]].decode(), re.M), 'Class name is not declared by exact packed script')
    packed_uids = uid_cache(resources['.godot/uid_cache.bin'])
    require(packed_uids == {path: value for path, value in uid_cache((stage / '.godot/uid_cache.bin').read_bytes()).items()
                           if path in source_paths}, 'Packed UID cache differs from staged resource identities')
    require('res://diagnostics/linux_profile_overhead.gd' in packed_uids, 'Missing fixture UID cache identity')
    result.update(project=project_properties(resources['project.binary']), imported_resources=imported,
                  uid_cache=packed_uids, global_classes=packed_classes,
                  ledger_sha256=sha(resources['diagnostics/source_ledger.json']), text_source_paths=sorted(expected))
    expected.update(('.godot/global_script_class_cache.cfg', '.godot/uid_cache.bin', 'project.binary'))
    require(set(resources) == expected, 'Unexpected or missing pack resources: ' + repr(sorted(set(resources) ^ expected)))
    return result, pack
