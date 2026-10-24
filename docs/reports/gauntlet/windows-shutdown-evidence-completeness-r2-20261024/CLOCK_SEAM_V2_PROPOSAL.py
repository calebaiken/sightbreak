"""UNEXECUTED fixture-only clock proposal; no production import or native time."""
import math


class DeclaredClock:
    """One explicit synthetic schedule per collection, not a timing measurement.

    Reads never advance time. Only the declared operation graph may advance it.
    perf_counter has a different origin: only its own differences are meaningful.
    """
    def __init__(self):
        self.origin_ns=1000*10**9
        self.now_ns=self.origin_ns
        self.wall_origin_ns=1792800000*10**9
        self.perf_origin_ns=200000*10**9
        self.wall_step_ns=0
    def monotonic(self):return self.now_ns/10**9
    def time_ns(self):return self.wall_origin_ns+self.now_ns-self.origin_ns+self.wall_step_ns
    def perf_counter(self):return (self.perf_origin_ns+self.now_ns-self.origin_ns)/10**9
    def advance(self,seconds):
        if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:
            raise ValueError('finite nonnegative declared duration required')
        self.now_ns+=round(seconds*10**9)
        return self.monotonic()
    def step_wall(self,nanoseconds):
        if type(nanoseconds) is not int:raise ValueError('integer declared wall step required')
        self.wall_step_ns+=nanoseconds
