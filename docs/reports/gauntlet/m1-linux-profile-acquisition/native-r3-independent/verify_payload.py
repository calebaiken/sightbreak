#!/usr/bin/env python3
"""Independent read-only ELF/PCK/resource/ECFG reconstruction; no builder import."""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import struct

RAW = Path('/workspace/sightbreak-linux-packed-import-boundary/builds/linux-profile-acquisition-r3')
REPORT = Path(__file__).resolve().parent
TEMPLATE = Path('/workspace/sightbreak/.local/data/godot/export_templates/4.7.2.stable/linux_debug.x86_64')
checks = []


def need(value, name):
    checks.append({'name': name, 'passed': bool(value)})
    if not value:
        raise AssertionError(name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'unique JSON field ' + key)
            result[key] = value
        return result
    result = json.loads(text, object_pairs_hook=unique,
                        parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    def finite(value):
        if type(value) is float:
            need(math.isfinite(value), 'finite JSON number')
        elif isinstance(value, dict):
            for item in value.values(): finite(item)
        elif isinstance(value, list):
            for item in value: finite(item)
    finite(result)
    return result


class Cursor:
    def __init__(self, raw): self.raw, self.at = raw, 0
    def take(self, count):
        need(0 <= count <= len(self.raw) - self.at, 'binary read within bounds')
        value = self.raw[self.at:self.at + count]; self.at += count
        return value
    def unpack(self, pattern): return struct.unpack(pattern, self.take(struct.calcsize(pattern)))
    def string(self):
        count, = self.unpack('<I'); need(count <= 1048576, 'bounded string')
        text = self.take(count).decode('utf-8'); need('\0' not in text, 'string has no embedded NUL')
        return text
    def end(self): need(self.at == len(self.raw), 'binary fully consumed')


def safe(name):
    need(bool(name) and not name.startswith('/') and '\\' not in name and '\0' not in name
         and name == PurePosixPath(name).as_posix() and
         all(part not in ('', '.', '..', 'tests') for part in name.split('/')), 'safe unique resource path ' + name)
    return name


def elf(data):
    need(data[:7] == b'\x7fELF\x02\x01\x01' and struct.unpack_from('<HHI', data, 16) == (2, 62, 1), 'ELF64 LE x86_64')
    phoff, shoff = struct.unpack_from('<QQ', data, 32)
    eh, phs, phn, shs, shn, sn = struct.unpack_from('<6H', data, 52)
    need((eh, phs, shs) == (64, 56, 64) and 0 < sn < shn < 10000 and
         phoff + phs * phn <= len(data) and shoff + shs * shn <= len(data), 'ELF header/table dimensions')
    for n in range(phn):
        row = struct.unpack_from('<II6Q', data, phoff + n * phs)
        need(row[2] + row[5] <= len(data), 'ELF program segment bound')
    a, n = struct.unpack_from('<QQ', data, shoff + sn * shs + 24); names = data[a:a+n]
    need(a+n <= len(data), 'ELF name table bound'); result = {}
    for i in range(shn):
        at = shoff+i*shs; row = struct.unpack_from('<II4Q2I2Q', data, at)
        need(row[0] < len(names) and names.find(b'\0', row[0]) >= 0, 'ELF section name bound')
        name = names[row[0]:names.find(b'\0', row[0])].decode()
        need(name not in result and (row[1] == 8 or row[4]+row[5] <= len(data)), 'ELF unique bounded section ' + name)
        result[name] = (at, row[4], row[5])
    return result


def sections(raw, packed=False):
    if packed:
        need(raw.endswith(b'\n\0') and raw.count(b'\0') == 1, 'packed import LF plus one terminal NUL')
        raw = raw[:-1]
    text = raw.decode('utf-8')
    need(not any(ord(c) < 32 and c != '\n' or 127 <= ord(c) < 160 for c in text), 'import raw control exclusion')
    result, current, pending = {}, None, []
    def flush():
        if pending:
            key, value = '\n'.join(pending).split('=', 1)
            need(current is not None and key not in result[current], 'import assignment unique and in section')
            result[current][key] = strict(value); pending.clear()
    for line in text.splitlines():
        if not line.strip() or line.startswith(';'): continue
        if re.fullmatch(r'\[[a-z_]+\]', line):
            flush(); current = line[1:-1]; need(current not in result, 'unique import section'); result[current] = {}
        elif re.match(r'^[A-Za-z_][A-Za-z_0-9/.]*=', line): flush(); pending.append(line)
        else: need(bool(pending), 'import continuation has assignment'); pending.append(line)
    flush(); return result


def uids(raw):
    cur = Cursor(raw); count, = cur.unpack('<I'); need(count < 10000, 'UID count bound'); result = {}
    for _ in range(count):
        uid, = cur.unpack('<Q'); path = cur.string()
        need(path.startswith('res://') and path not in result and uid not in result.values(), 'UID unique path/id')
        safe(path[6:]); result[path] = uid
    cur.end(); return result


def classes(raw):
    text = raw.decode('utf-8').strip(); need(text.startswith('list='), 'class cache list prefix')
    rows = strict(re.sub(r'&(?=")', '', text[5:])); need(type(rows) is list, 'class cache list type'); result = {}
    for row in rows:
        need(type(row) is dict and row.get('language') == 'GDScript' and type(row.get('class')) is str, 'class entry shape')
        path = row['path']; need(path.startswith('res://') and path not in result, 'class unique source path')
        safe(path[6:]); result[path] = row
    return result


def scalar(raw):
    cur = Cursor(raw); kind, = cur.unpack('<I')
    if kind == 1:
        value, = cur.unpack('<I'); need(value in (0, 1), 'Variant bool'); value = bool(value)
    elif kind in (2, 65538): value, = cur.unpack('<q' if kind == 65538 else '<i')
    elif kind in (3, 65539):
        value, = cur.unpack('<d' if kind == 65539 else '<f'); need(math.isfinite(value), 'Variant finite float')
    elif kind == 4:
        value = cur.string(); need(not any(cur.take((-cur.at) % 4)), 'Variant zero padding')
    else: raise AssertionError('Unsupported critical Variant ' + str(kind))
    cur.end(); return value


def main():
    data = (RAW/'export/linux-profile-diagnostic.x86_64').read_bytes(); template = TEMPLATE.read_bytes()
    ex, tm = elf(data), elf(template); length, magic = struct.unpack_from('<QI', data, len(data)-12)
    start = len(data)-12-length; need(magic == 0x43504447 and start == len(template) and length > 104, 'PCK trailer/template EOF')
    at, off, size = ex['pck']; need((at, off, size) == (tm['pck'][0], start, length+12), 'only registered ELF PCK fixup')
    prefix = bytearray(data[:start]); prefix[at+24:at+40] = template[at+24:at+40]; need(prefix == template, 'pinned template prefix')
    pack = data[start:-12]; header = struct.unpack_from('<6I2Q', pack)
    need(header[:7] == (0x43504447, 4, 4, 7, 2, 2, 104) and 104 <= header[7] < length and not any(pack[40:104]), 'PCK version/flags/base/reserved')
    cur = Cursor(pack[header[7]:]); count, = cur.unpack('<I'); need(0 < count < 10000, 'PCK count bound')
    resources, table, ranges = {}, [], []
    for _ in range(count):
        n, = cur.unpack('<I'); need(0 < n <= 16384 and n%4 == 0, 'PCK padded path bound')
        name = safe(cur.take(n).rstrip(b'\0').decode('utf-8')); offset, size, md5, flags = cur.unpack('<QQ16sI')
        begin, end = 104+offset, 104+offset+size
        need(name not in resources and flags == 0 and 104 <= begin < end <= header[7], 'PCK bounded unique resource')
        raw = pack[begin:end]; need(hashlib.md5(raw).digest() == md5, 'resource MD5 integrity ' + name)
        resources[name] = raw; ranges.append((begin,end)); table.append({'path':name,'bytes':size,'sha256':sha(raw),'md5':md5.hex(),'pack_offset':begin})
    need(not any(cur.take(len(cur.raw)-cur.at)), 'zero PCK directory tail')
    need(all(a[1] <= b[0] for a,b in zip(sorted(ranges),sorted(ranges)[1:])), 'PCK no resource overlap')
    record = strict((RAW/'diagnostic-stage.json').read_bytes()); stage = RAW/'project'; expected, paths, imports = set(),set(),[]
    for name,wanted in record['files'].items():
        raw = (stage/name).read_bytes(); need({'bytes':len(raw),'sha256':sha(raw)} == wanted, 'frozen staged bytes ' + name)
        if Path(name).suffix in ('.gd','.tscn','.tres','.gdshader') or name == 'diagnostics/source_ledger.json':
            need(resources.get(name) == raw,'exact packed text ' + name); expected.add(name); paths.add('res://'+name)
        if name.endswith('.import'):
            original, exported = sections(raw), sections(resources[name],True)
            need(set(original) == {'remap','deps','params'} and set(exported) == {'remap'},'exact import section sets')
            remap = {k:v for k,v in original['remap'].items() if not k.startswith('path.') or k == 'path.s3tc'}
            need(exported['remap'] == remap,'packed/staged remap equality ' + name)
            source = name[:-7]; need(source in record['files'] and original['deps']['source_file'] == 'res://'+source,'bound import source')
            expected.add(name); paths.add('res://'+source)
            for key,target in remap.items():
                if key == 'path' or key.startswith('path.'):
                    need(target.startswith('res://.godot/imported/'),'safe import target prefix'); target = safe(target[6:])
                    need(resources[target] == (stage/target).read_bytes(),'exact packed/staged cache '+target); expected.add(target)
                    imports.append({'source':source,'source_sha256':record['files'][source]['sha256'],'target':target,'cache_sha256':sha(resources[target])})
    need(resources['assets/icon.svg'] == (stage/'assets/icon.svg').read_bytes(),'forced icon equality'); expected.add('assets/icon.svg')
    ledger = strict(resources['diagnostics/source_ledger.json']); need(ledger['source'] == record['source'] and ledger['content'] == record['base_files'],'source ledger provenance')
    need(sha(resources['diagnostics/linux_profile_overhead.gd']) == record['source']['fixture_sha256'] and sha(resources['diagnostics/linux_profile_overhead.tscn']) == record['source']['scene_sha256'],'fixture/scene source pins')
    auxiliary = {n:(stage/n).read_bytes() for n in ('.godot/global_script_class_cache.cfg','.godot/uid_cache.bin')}
    pc = classes(resources['.godot/global_script_class_cache.cfg']); pu = uids(resources['.godot/uid_cache.bin'])
    need(pc == {k:v for k,v in classes(auxiliary['.godot/global_script_class_cache.cfg']).items() if k in paths},'filtered packed class cache')
    for path,row in pc.items(): need(re.search(r'^class_name\s+'+re.escape(row['class'])+r'\b',resources[path[6:]].decode(),re.M),'packed class declaration '+path)
    need(pu == {k:v for k,v in uids(auxiliary['.godot/uid_cache.bin']).items() if k in paths} and 'res://diagnostics/linux_profile_overhead.gd' in pu,'filtered packed UID cache/fixture identity')
    critical = {'application/run/main_scene':'res://diagnostics/linux_profile_overhead.tscn','display/window/size/viewport_width':1280,'display/window/size/viewport_height':720,'display/window/size/window_width_override':1280,'display/window/size/window_height_override':720,'rendering/renderer/rendering_method':'gl_compatibility','rendering/renderer/rendering_method.mobile':'gl_compatibility','rendering/anti_aliasing/quality/msaa_3d':1,'rendering/driver/threads/thread_model':1,'debug/settings/stdout/print_gpu_profile':False,'editor/export/convert_text_resources_to_binary':False}
    defaults = {'rendering/driver/threads/thread_model':1,'debug/settings/stdout/print_gpu_profile':False}; bases = {k.split('.',1)[0] for k in critical}; declared = {}; section = None
    for line in (stage/'project.godot').read_text().splitlines():
        if re.fullmatch(r'\[[a-z_]+\]',line): section = line[1:-1]
        elif section and '=' in line and not line.lstrip().startswith(';'):
            key,value = line.split('=',1); key = section+'/'+key; base = key.split('.',1)[0]
            if base in bases:
                need(key not in declared,'unique critical staged selector'); declared[key] = strict(value)
                need(type(declared[key]) is type(critical[base]) and declared[key] == critical[base],'critical staged selector value '+key)
    need(set(critical) <= set(declared),'all required critical staged keys')
    cur = Cursor(resources['project.binary']); need(cur.take(4) == b'ECFG','ECFG header'); n, = cur.unpack('<I'); need(0 < n < 10000,'ECFG property count'); props = {}
    for _ in range(n):
        key = cur.string(); size, = cur.unpack('<I'); need(key not in props,'ECFG unique property'); props[key] = cur.take(size)
    cur.end(); need(all(k in declared for k in props if k.split('.',1)[0] in bases),'no undeclared critical packed selector')
    project = {}
    for k,wanted in declared.items():
        value = scalar(props[k]) if k in props else defaults.get(k)
        need(type(value) is type(wanted) and value == wanted,'critical ECFG scalar '+k); project[k] = value
    expected |= {'.godot/global_script_class_cache.cfg','.godot/uid_cache.bin','project.binary'}
    need(set(resources) == expected and len(resources) == 94,'complete exact 94-resource set')
    result = {'ELF_sha256':sha(data),'ELF_bytes':len(data),'PCK_start':start,'PCK_bytes':length,'PCK_sha256':sha(pack),'PCK_header':list(header),'template_sha256':sha(template),'resources':table,'project':project,'imported_resources':imports,'stage_auxiliary':{k:{'bytes':len(v),'sha256':sha(v)} for k,v in auxiliary.items()},'uid_cache':pu,'global_classes':pc,'ledger_sha256':sha(resources['diagnostics/source_ledger.json']),'text_source_paths':sorted(expected-{'.godot/global_script_class_cache.cfg','.godot/uid_cache.bin','project.binary'})}
    need(result == strict((RAW/'independent-payload.json').read_bytes()),'independently reconstructed complete payload receipt equals original')
    need(pack == (RAW/'embedded-diagnostic.pck').read_bytes(),'original retained embedded PCK exact equality')
    (REPORT/'payload-independent-readback.json').write_text(json.dumps({'passed':True,'checks':checks,'result':result},indent=2)+'\n')
    print(json.dumps({'passed':True,'predicates':len(checks),'resources':len(resources),'ELF':sha(data),'PCK':sha(pack)}))


if __name__ == '__main__': main()
