import ctypes as C
import time

def key_pulse(self, names, seconds, *, deadline, receipt, clock=time.monotonic, sleep=time.sleep):
    """Route-only in-process dispatch; receipts are API/OS observations.

    All evidence stays in memory until attempted keys have been released.
    SendInput return and OS bitmaps do not prove game consumption or a
    physical hold interval. Existing key() schedules remain unchanged.
    """
    receipt.update(status='IN_PROGRESS', keys=list(names) if isinstance(names, (tuple, list)) else names, requested_seconds=seconds,
                   absolute_deadline=deadline, edges=[], os_states=[], down_checks=[], attempted_keys=[],
                   released_keys=[], release_errors=[], release_complete=False,
                   scope='in-process SendInput API brackets and GetAsyncKeyState; gameplay unverified')
    attempted, failure = [], None
    pinned_window, pinned_pid = self.window, self.pid

    def budget():
        if clock() >= deadline:
            raise TimeoutError('Original route deadline expired during native key pulse')

    def state(label, samples=None):
        begin = clock()
        owner = C.c_uint32()
        visible = bool(self.window and self.user.IsWindowVisible(self.window))
        thread = self.user.GetWindowThreadProcessId(self.window, C.byref(owner)) if self.window else 0
        foreground = self.user.GetForegroundWindow()
        value = {'label': label, 'read_begin_monotonic': begin, 'read_end_monotonic': clock(),
                 'target_window': self.window, 'expected_pid': self.pid, 'window_pid': owner.value,
                 'window_thread': thread, 'visible': visible, 'foreground_window': foreground,
                 'keys_down': {name: bool(self.user.GetAsyncKeyState(ord(name.upper())) & 0x8000)
                               for name in ('w', 'a', 's', 'd')},
                 'lmb_down': bool(self.user.GetAsyncKeyState(0x01) & 0x8000)}
        value['read_end_monotonic'] = clock()
        (receipt['os_states'] if samples is None else samples).append(value)
        if (self.window != pinned_window or self.pid != pinned_pid
                or not visible or not thread or type(pinned_pid) is not int or pinned_pid <= 0
                or owner.value != pinned_pid or foreground != pinned_window):
            raise RuntimeError('Native route pulse lost its owned visible focused window')
        return value

    def edge(name, down):
        row = {'key': name, 'down': down, 'before_monotonic': clock()}
        receipt['edges'].append(row)
        try:
            self.key(name, down)
        except BaseException as error:
            row['error'] = type(error).__name__ + ': ' + str(error)
            raise
        finally:
            row['after_monotonic'] = clock()

    try:
        if (not isinstance(names, (tuple, list)) or not 1 <= len(names) <= 2
                or any(type(name) is not str or name not in ('w', 'a', 's', 'd') for name in names)
                or len(set(names)) != len(names)
                or {'w', 's'} <= set(names) or {'a', 'd'} <= set(names)
                or type(seconds) not in (int, float) or not 0 < seconds <= 2.5
                or type(deadline) not in (int, float) or not float('-inf') < deadline < float('inf')):
            raise RuntimeError('Invalid bounded native route key pulse')
        budget()
        before = state('before_down')
        if before['lmb_down'] or any(before['keys_down'].values()):
            raise RuntimeError('Native route key pulse requires physically neutral controls')
        budget()
        receipt['hold_until_monotonic'] = min(clock() + seconds, deadline)
        try:
            for name in names:
                budget()
                check = {'key': name, 'owned_keys': list(attempted), 'os_states': [],
                         'read_begin_monotonic': clock(), 'status': 'IN_PROGRESS'}
                receipt['down_checks'].append(check)
                try:
                    current = state('before_key_down', check['os_states'])
                    if (current['lmb_down'] or any(down and key not in attempted
                                                  for key, down in current['keys_down'].items())):
                        raise RuntimeError('Native route key pulse observed unowned controls before down')
                    budget()
                    if clock() >= receipt['hold_until_monotonic']:
                        raise TimeoutError('Native route checks exhausted its requested pulse window')
                    check['status'] = 'CHECKED'
                except BaseException as error:
                    check.update(status='FAILED', error_type=type(error).__name__, error=str(error))
                    raise
                finally:
                    check['read_end_monotonic'] = clock()
                attempted.append(name)
                receipt['attempted_keys'].append(name)
                edge(name, True)
            state('after_down')
            budget()
            wait = receipt['hold_until_monotonic'] - clock()
            if wait <= 0:
                raise TimeoutError('Native route dispatch exhausted its requested pulse window')
            sleep(wait)
            if clock() < receipt['hold_until_monotonic']:
                raise RuntimeError('Native route pulse sleep returned before its requested boundary')
        except BaseException as error:
            failure = error
        finally:
            for name in attempted:
                try:
                    edge(name, False)
                    receipt['released_keys'].append(name)
                except BaseException as error:
                    receipt['release_errors'].append(type(error).__name__ + ': ' + str(error))
            try:
                after = state('after_release')
                receipt['release_complete'] = (not receipt['release_errors'] and not after['lmb_down']
                                               and not any(after['keys_down'].values()))
            except BaseException as error:
                receipt['release_errors'].append(type(error).__name__ + ': ' + str(error))
        if failure is not None:
            raise failure
        if receipt['release_errors'] or not receipt['release_complete']:
            raise RuntimeError('Native route pulse could not verify OS control release')
        budget()
        receipt.update(status='API_RETURNED_WITH_OS_RELEASE', finished_monotonic=clock())
        return receipt
    except BaseException as error:
        receipt.update(status='FAILED', error_type=type(error).__name__, error=str(error),
                       finished_monotonic=clock())
        raise
