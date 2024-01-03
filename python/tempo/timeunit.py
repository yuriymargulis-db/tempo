from typing import NamedTuple
from functools import total_ordering


@total_ordering
class TimeUnit(NamedTuple):
    name: str
    approx_seconds: float
    sub_second_precision: int = 0
    """
    Represents a unit of time, with a name,
    an approximate number of seconds,
    and a sub-second precision.
    """

    def __eq__(self, other):
        return self.approx_seconds == other.approx_seconds

    def __lt__(self, other):
        return self.approx_seconds < other.approx_seconds


TimeUnitsType = NamedTuple("TimeUnitsType",
                           [("YEARS", TimeUnit),
                            ("MONTHS", TimeUnit),
                            ("WEEKS", TimeUnit),
                            ("DAYS", TimeUnit),
                            ("HOURS", TimeUnit),
                            ("MINUTES", TimeUnit),
                            ("SECONDS", TimeUnit),
                            ("MILLISECONDS", TimeUnit),
                            ("MICROSECONDS", TimeUnit),
                            ("NANOSECONDS", TimeUnit)])

StandardTimeUnits = TimeUnitsType(
    TimeUnit("year", 365 * 24 * 60 * 60),
    TimeUnit("month", 30 * 24 * 60 * 60),
    TimeUnit("week", 7 * 24 * 60 * 60),
    TimeUnit("day", 24 * 60 * 60),
    TimeUnit("hour", 60 * 60),
    TimeUnit("minute", 60),
    TimeUnit("second", 1),
    TimeUnit("millisecond", 1e-03, 3),
    TimeUnit("microsecond", 1e-06, 6),
    TimeUnit("nanosecond", 1e-09, 9)
)
