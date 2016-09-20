#! /usr/bin/env python3

import contextlib
import enum
import io
import subprocess
import itertools

from datetime import datetime, timedelta


@contextlib.contextmanager
def _command_context(*args):
    process = subprocess.Popen(args, stdout=subprocess.PIPE)

    try:
        yield process
    finally:
        process.kill()
        process.wait()


class _EventType(enum.Enum):
    sleep = 'sleep'
    wake = 'wake'


def _iter_events(lines_iter):
    for i in lines_iter:
        fields, *_ = i.split('\t')

        try:
            time = datetime.strptime(
                fields[:25],
                '%Y-%m-%d %H:%M:%S %z')
        except ValueError:
            continue

        type = _EventType.__members__.get(fields[26:].strip().lower())

        if type is not None:
            # print(time, type)
            yield time, type


def _iter_wake_periods(events_iter):
    last_wake_time = None

    for time, type in events_iter:
        if type == _EventType.sleep:
            if last_wake_time is not None:
                yield last_wake_time, time

                last_wake_time = None
        elif type == _EventType.wake:
            if last_wake_time is None:
                last_wake_time = time


def _filter_short_wake_periods(wake_periods_iter, *, min_duration):
    for a, b in wake_periods_iter:
        if b - a > min_duration:
            yield a, b


def _filter_short_sleep_periods(wake_periods_iter, *, min_duration):
    previous_period = None

    for i in wake_periods_iter:
        if previous_period is None:
            previous_period = i
        else:
            previous_a, previous_b = previous_period
            current_a, current_b = i

            if current_a - previous_b > min_duration:
                yield previous_period

                previous_period = i
            else:
                previous_period = previous_a, current_b

    if not previous_period is None:
        yield previous_period


def _iter_filtered_wake_periods():
    with _command_context('pmset', '-g', 'log') as process:
        stdout = io.TextIOWrapper(io.BufferedReader(process.stdout), 'latin-1')

        yield from _filter_short_sleep_periods(
            _filter_short_wake_periods(
                _iter_wake_periods(
                    _iter_events(stdout)),
                min_duration=timedelta(minutes=10)),
            min_duration=timedelta(minutes=30))

        yield from _iter_wake_periods(_iter_events(stdout))


def intervals_by_date():
    return [
        (date, intervals)
        for (date, (*intervals,))
        in itertools.groupby(
            _iter_filtered_wake_periods(),
            key=lambda x: x[0].date())]
