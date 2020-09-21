import asyncio
import time

import pytest

import pbatch

from .conftest import PERFORMANCE_SLEEP_TIME

pytestmark = [pytest.mark.performance]


def test_postpone_performance():
    executed = finished = False

    def add(a, b, c=None):
        nonlocal executed, finished
        executed = True
        time.sleep(PERFORMANCE_SLEEP_TIME)
        finished = True
        return a + b + c

    assert not executed
    assert not finished

    postponement = pbatch.postpone(add, 1, 2, c=100)

    assert executed
    assert not finished

    time.sleep(PERFORMANCE_SLEEP_TIME / 2)

    start = time.time()
    assert postponement.wait() == 103
    end = time.time()

    duration = end - start
    assert duration < PERFORMANCE_SLEEP_TIME

    assert executed
    assert finished

    assert postponement.wait() == 103


def test_cancel():
    executed = False

    def long_function():
        nonlocal executed
        executed = True
        time.sleep(PERFORMANCE_SLEEP_TIME)

    start = time.time()

    postponement = pbatch.postpone(long_function)
    postponement.cancel()

    with pytest.raises(asyncio.CancelledError) as info:
        postponement.wait()
    assert info.value.args == ()

    end = time.time()
    duration = end - start
    assert duration < PERFORMANCE_SLEEP_TIME

    assert executed
