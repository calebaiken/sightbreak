#!/usr/bin/env python3
"""Bounded native filesystem API probe, not a gameplay or acceptance test.

Keeps the failing S7 suite intact and distinguishes its os.replace operation
from pinned Godot's DeleteFileW(destination), MoveFileW(source, destination).
Every operation uses fresh files; a failure is a measured probe outcome.
"""
import argparse
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

from native_observation import open_shared_text


OLD = b'{"generation":1}'
NEW = b'{"generation":2}'


def error_record(error):
    return {'type': type(error).__name__, 'winerror': getattr(error, 'winerror', None),
            'errno': getattr(error, 'errno', None), 'message': str(error)}


def attempt(call):
    try:
        value = call()
        return {'ok': True, 'value': value}
    except OSError as error:
        return {'ok': False, 'error': error_record(error)}


class Windows:
    def __init__(self):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateFileW': ([wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                             ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                             wintypes.HANDLE], wintypes.HANDLE),
            'CloseHandle': ([wintypes.HANDLE], wintypes.BOOL),
            'ReadFile': ([wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                          ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p], wintypes.BOOL),
            'MoveFileW': ([wintypes.LPCWSTR, wintypes.LPCWSTR], wintypes.BOOL),
            'MoveFileExW': ([wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD], wintypes.BOOL),
            'DeleteFileW': ([wintypes.LPCWSTR], wintypes.BOOL),
            'ReplaceFileW': ([wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                              wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p], wintypes.BOOL),
            'SetFileInformationByHandle': ([wintypes.HANDLE, ctypes.c_int,
                                            ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = arguments, result

    def checked(self, name, *arguments):
        if not getattr(self.kernel, name)(*arguments):
            raise ctypes.WinError(ctypes.get_last_error())

    def open(self, path, *, access=0x80000000, share=7):
        handle = self.kernel.CreateFileW(str(path), access, share, None, 3, 0x80, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def read(self, handle):
        buffer, count = ctypes.create_string_buffer(128), wintypes.DWORD()
        self.checked('ReadFile', handle, buffer, 128, ctypes.byref(count), None)
        return buffer.raw[:count.value].decode('utf-8')

    @contextmanager
    def reader(self, path, style):
        if style == 'ordinary-path-open':
            with path.open('r', encoding='utf-8') as stream:
                yield stream.read
        elif style == 'helper-textio-share7':
            with open_shared_text(path) as stream:
                yield stream.read
        elif style == 'crt-fileio-share7':
            import msvcrt
            handle = self.open(path)
            try:
                descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY | os.O_NOINHERIT)
            except BaseException:
                self.checked('CloseHandle', handle)
                raise
            with io.FileIO(descriptor, mode='rb', closefd=True) as stream:
                yield lambda: stream.read().decode('utf-8')
        else:
            handle = self.open(path, share=3 if style == 'raw-share3' else 7)
            try:
                yield lambda: self.read(handle)
            finally:
                self.checked('CloseHandle', handle)

    def posix_replace(self, source, destination):
        # FileRenameInfoEx = 22. Flags REPLACE_IF_EXISTS | POSIX_SEMANTICS = 3.
        class RenameInformation(ctypes.Structure):
            _fields_ = [('Flags', wintypes.DWORD), ('RootDirectory', wintypes.HANDLE),
                        ('FileNameLength', wintypes.DWORD), ('FileName', wintypes.WCHAR * 1)]
        encoded = str(destination.resolve()).encode('utf-16-le')
        size = max(ctypes.sizeof(RenameInformation), RenameInformation.FileName.offset + len(encoded))
        buffer = ctypes.create_string_buffer(size)
        information = RenameInformation.from_buffer(buffer)
        information.Flags, information.FileNameLength = 3, len(encoded)
        ctypes.memmove(ctypes.addressof(buffer) + RenameInformation.FileName.offset, encoded, len(encoded))
        handle = self.open(source, access=0x00010000)
        try:
            self.checked('SetFileInformationByHandle', handle, 22, buffer, size)
        finally:
            self.checked('CloseHandle', handle)

    def operation(self, name, source, destination):
        if name == 'os.replace':
            os.replace(source, destination)
        elif name == 'MoveFileExW-replace':
            self.checked('MoveFileExW', str(source), str(destination), 1)
        elif name == 'ReplaceFileW':
            self.checked('ReplaceFileW', str(destination), str(source), None, 0, None, None)
        elif name == 'godot-DeleteFileW-then-MoveFileW':
            stages = {'delete': attempt(lambda: self.checked('DeleteFileW', str(destination)))}
            if stages['delete']['ok']:
                stages['move'] = attempt(lambda: self.checked('MoveFileW', str(source), str(destination)))
            return stages
        elif name == 'rename-old-aside-then-install':
            backup = destination.with_name('unique-old-generation.json')
            stages = {'rename_old': attempt(lambda: self.checked('MoveFileW', str(destination), str(backup)))}
            if stages['rename_old']['ok']:
                stages['install'] = attempt(lambda: self.checked('MoveFileW', str(source), str(destination)))
                stages['delete_backup'] = attempt(lambda: self.checked('DeleteFileW', str(backup)))
            return stages
        elif name == 'FileRenameInfoEx-posix-replace':
            self.posix_replace(source, destination)
        else:
            raise ValueError(name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if os.name != 'nt':
        raise SystemExit('This diagnostic must execute natively on Windows')
    args.output.mkdir(parents=True, exist_ok=False)
    baseline = subprocess.run([sys.executable, 'scripts/test_native_observation.py', '-v'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    (args.output / 's7-contract-test.log').write_bytes(baseline.stdout)
    report = {'scope': 'Native Windows filesystem API diagnostic; no acceptance or gameplay claim',
              'platform': platform.platform(), 'python': sys.version,
              'source_commit': os.environ.get('GITHUB_SHA'),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              's7_unchanged_contract_suite_exit': baseline.returncode, 'cases': []}
    windows = Windows()
    for style in ('ordinary-path-open', 'raw-share3', 'raw-share7', 'crt-fileio-share7', 'helper-textio-share7'):
        for operation in ('os.replace', 'MoveFileExW-replace', 'ReplaceFileW',
                          'godot-DeleteFileW-then-MoveFileW', 'rename-old-aside-then-install',
                          'FileRenameInfoEx-posix-replace'):
            with tempfile.TemporaryDirectory(prefix='sightbreak-observation-probe-') as temporary:
                destination, source = Path(temporary) / 'statüs.json', Path(temporary) / 'status.json.tmp'
                destination.write_bytes(OLD)
                source.write_bytes(NEW)
                row = {'reader': style, 'operation': operation}
                with windows.reader(destination, style) as read:
                    row['operation_result'] = attempt(lambda: windows.operation(operation, source, destination))
                    row['old_handle_content'] = attempt(read)
                    row['destination_while_open'] = attempt(lambda: destination.read_text(encoding='utf-8'))
                row['destination_after_close'] = attempt(lambda: destination.read_text(encoding='utf-8'))
                row['source_after_close'] = attempt(lambda: source.read_text(encoding='utf-8'))
                report['cases'].append(row)
                print(json.dumps(row, ensure_ascii=True), flush=True)
    (args.output / 'probe.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'cases'}), flush=True)


if __name__ == '__main__':
    main()
