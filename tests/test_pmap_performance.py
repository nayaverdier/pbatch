import time

import pytest

import pbatch

from .conftest import PERFORMANCE_SLEEP_TIME

pytestmark = [pytest.mark.performance]


PERFORMANCE_ITEMS = range(10)


def time_list(f, *args, **kwargs):
    start = time.time()
    result = list(f(*args, **kwargs))
    end = time.time()
    return result, (end - start)


@pytest.mark.parametrize("include_power", [True, False])
@pytest.mark.parametrize("chunk_size", [2, 3, 4, 5, 6, 7, 8, 9, 10, 100, None])
def test_pmap_performance(include_power, chunk_size):
    def sleep_exp(x, power=2):
        time.sleep(PERFORMANCE_SLEEP_TIME)
        return x ** power

    max_time = PERFORMANCE_SLEEP_TIME * len(PERFORMANCE_ITEMS)

    if include_power:
        powers = [3] * len(PERFORMANCE_ITEMS)
        results, duration = time_list(pbatch.pmap, sleep_exp, PERFORMANCE_ITEMS, powers, chunk_size=chunk_size)
    else:
        results, duration = time_list(pbatch.pmap, sleep_exp, PERFORMANCE_ITEMS, chunk_size=chunk_size)

    if include_power:
        assert results == [0, 1, 8, 27, 64, 125, 216, 343, 512, 729]
    else:
        assert results == [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

    assert duration < max_time
