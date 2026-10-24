# Windows math acquisition: exact public-source research

Source-only builder support. CPython reference is exactly v3.12.10; Godot reference is ed1daf0bf. No Godot/native/version invocation, Windows API call, helper, test, acquisition, CI, SDK download or binary inspection ran. Network/source-reader commands used CPU4. This report is outside all existing branches and contains no implementation. Source does not establish runtime success.

## CPython v3.12.10

- `Python/fileutils.c:2716-2745`: `_Py_set_blocking` gets the Windows handle, queries pipe state and changes PIPE_NOWAIT through SetNamedPipeHandleState. Failure raises an exception. `Modules/posixmodule.c:14608-14618` is the os.set_blocking wrapper. `Doc/library/os.rst:1643-1660` explicitly limits Windows support to pipes and dates support to 3.12.
- `Python/fileutils.c:1877-1883`: a nonblocking empty pipe's CRT EINVAL / ERROR_NO_DATA maps to EAGAIN. Thus BlockingIOError is temporary emptiness, not EOF. Other read failures remain errors.
- `Lib/subprocess.py:1015-1024`: parent stdout/stderr are binary io.open handles unless text mode wraps them. Fixed-size os.read on the raw descriptors avoids buffered-reader ownership and unbounded read-all operations.
- `Lib/subprocess.py:1374-1407`: stdout/stderr PIPE requests create pipe pairs; the child-facing ends are duplicated inheritable. `_make_inheritable` is 1414-1420.
- `Lib/subprocess.py:1475-1507`: STARTF_USESTDHANDLES supplies all three handles. With close_fds and standard handles, the explicit inherited handle list contains those standard handles; internal close_fds becomes false because CreateProcess must inherit that constrained list. This does not mean arbitrary parent handles are intentionally inherited.
- `Lib/subprocess.py:1536-1555`: CreateProcess receives the inheritance flag, and the parent closes its copies of child-only pipe ends. The source explicitly warns retained parent write ends would prevent closure and hang ReadFile.
- `Lib/subprocess.py:1557-1561`: Popen retains the process HANDLE in `_handle` and closes the initial thread HANDLE. `1574-1595`: poll/wait query the process handle and return exit status; these methods do not drain or close stdout/stderr. Root exit and both pipe EOFs are independent acquisition conditions. Descendant writers can keep pipes open after the root exits.
- `Lib/subprocess.py:1598-1618`: Windows communicate uses daemon reader threads with fh.read(), not bounded chunks. `1624-1634`: timeout intentionally leaves reader threads and descriptors open for another communicate call. It is unsuitable as an unmodified bounded-retention transport.

Concrete constraints: require successful nonblocking setup, bound bytes read per stream and per polling iteration, preserve original operation/cleanup deadlines, treat EAGAIN separately from EOF, drain both streams fairly, surface errors and overflow, and retain explicit process-exit/EOF/handle-close states. No selector-based Windows pipe claim follows from these facts. No reader-thread or Windows API cancellation implementation is proposed in this report.

## Godot ed1daf0bf

- `platform/windows/windows_terminal_logger.cpp:42-75`: 1024 bytes is only the initial formatting buffer. Messages at least that long allocate len+1 bytes and are formatted again. CR/LF is normalized to CRLF; output is sent through WriteFile(GetStdHandle(stdout/stderr)). The return value and written byte count are not checked here. There is no intentional 1024-byte truncation cap, but source alone does not prove complete delivery.
- `core/io/logger.cpp:185-220`: RotatedFileLogger likewise has a 512-byte initial buffer and grows dynamically. It stores the formatted message (ANSI removal when regex support exists), flushes error output or configured stdout flushes, and has no total-byte or per-file byte cap.
- `core/io/logger.cpp:110-175`: rotation limits backup count when a logger is opened; max_files is at least one. This is count retention, not size-based rotation. No aggregate disk bound is enforced here.
- `main/main.cpp:2312-2339`: desktop file logging defaults on with `user://logs/godot.log` and max_log_files=5. Explicit --log-file enables the selected path even if project file logging is disabled and sets max_files=1, disabling backup rotation. It does not impose a byte limit.
- `main/main.cpp:2363-2378`: application/run/disable_stdout and disable_stderr suppress output; quiet mode disables print lines. These must not be mistaken for harmless output-collection flags.
- `platform/windows/os_windows.cpp:2417-2438,2508-2509`: config/data use APPDATA (or '.' if absent); cache uses LOCALAPPDATA, then temporary-path fallback. `core/os/os.cpp:338-352`: default user:// is APPDATA/Godot/app_userdata/<safe project name>; custom-user-dir settings change this, and unnamed projects use [unnamed project].
- `platform/windows/os_windows.cpp:149-183`: console attachment saves/restores inherited standard handles and avoids replacing already-valid CRT pipe/file redirection. This is source intent, not proof for any future process environment.

Consequences: file-logging count limits do not bound bytes. Pipe retention limits do not bound userdata log files. Isolate APPDATA and LOCALAPPDATA and inventory whatever state/log files are actually produced. Do not assume a 512/1024-byte Godot message ceiling or that root exit proves pipe completion.

## Exact fetched source identity

| Source | URL | SHA-256 |
|---|---|---|
| CPython fileutils.c | https://raw.githubusercontent.com/python/cpython/v3.12.10/Python/fileutils.c | 0742dd5d83b9e1b2642feb09de9a4489e84272d96e16309f44362deb278df652 |
| CPython subprocess.py | https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/subprocess.py | 85d29b2bf0249f5436838298c9a60ee93508b1102e9ac43b001f8a7e7ae8f375 |
| CPython posixmodule.c | https://raw.githubusercontent.com/python/cpython/v3.12.10/Modules/posixmodule.c | a8f1410ad95326648a473672ee3bf8158a5f744b7c032c0142327fb252688ab4 |
| CPython os.rst | https://raw.githubusercontent.com/python/cpython/v3.12.10/Doc/library/os.rst | 72ad4331b490fe71c62dca52f7ddd3fac4b24d10e5670d1a9091b87f496669c6 |
| Godot Windows terminal logger | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/platform/windows/windows_terminal_logger.cpp | e906c6d23c7b08504cbb3bc81e1f3f20d913d99c8bb98ed0357c158bbe6fd2c9 |
| Godot logger.cpp | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/core/io/logger.cpp | 0e62bdfbc75ee6eb99e208bc96d9cca847e3118db9b52b3081ad2dc6c784d6d7 |
| Godot os_windows.cpp | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/platform/windows/os_windows.cpp | cc6cdd8db3232ceee474ad3bc55fedb207d55be8e6d350fdbf04101101d11dd7 |
| Godot main.cpp | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/main/main.cpp | 1831257f5c8eb0707d278f04b21b1e4b3ba863f8dca5cab36022d4b19e36b8c1 |
| Godot core/os/os.cpp | https://raw.githubusercontent.com/godotengine/godot/ed1daf0bf/core/os/os.cpp | 9c5dab86487ea5dfa7391336510aec451717891f312cfec89aeb0a8b75a898f1 |
