import asyncio

import pytest

PERFORMANCE_SLEEP_TIME = 0.10


@pytest.yield_fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def implicit_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
