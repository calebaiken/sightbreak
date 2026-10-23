"""Read complete observation files without blocking their Godot producer.

Windows CRT opens normally omit FILE_SHARE_DELETE. A polling reader can then
make Godot's DeleteFileW-then-MoveFileW publication fail. These read-only handles
allow that sequence; an open reader still sees its original complete snapshot.
Windows publication has a missing-path interval, which callers already handle
under their existing stale-observation watchdog. This does not promise that
legacy Windows os.replace can replace an open destination.
"""
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path


MAX_OBSERVATION_BYTES = 2 * 1024 * 1024


@contextmanager
def _open_shared_binary(path):
    if os.name != 'nt':
        with Path(path).open('rb') as stream:
            yield stream
        return

    import ctypes
    from ctypes import wintypes
    import msvcrt

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    # GENERIC_READ; FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE;
    # OPEN_EXISTING; FILE_ATTRIBUTE_NORMAL. No write permission or inheritance.
    handle = kernel.CreateFileW(os.fspath(path), 0x80000000, 0x1 | 0x2 | 0x4,
                                None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY | os.O_NOINHERIT)
    except BaseException:
        kernel.CloseHandle(handle)
        raise
    # Ownership transfers to the CRT descriptor, then to the Python file. Each
    # failure path closes its current owner exactly once; never CloseHandle an
    # already-transferred handle.
    try:
        stream = os.fdopen(descriptor, 'rb')
    except BaseException:
        os.close(descriptor)
        raise
    with stream:
        yield stream


@contextmanager
def open_shared_text(path, *, encoding='utf-8'):
    with _open_shared_binary(path) as raw:
        with io.TextIOWrapper(raw, encoding=encoding, errors='strict') as stream:
            yield stream


def read_observation_json(path, *, max_bytes=MAX_OBSERVATION_BYTES):
    """Read one strict UTF-8 JSON snapshot with a byte bound and no retry."""
    if max_bytes <= 0:
        raise ValueError('Observation byte limit must be positive')
    with _open_shared_binary(path) as stream:
        payload = stream.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError('Observation exceeds its bounded byte budget')
    return json.loads(payload.decode('utf-8'))
