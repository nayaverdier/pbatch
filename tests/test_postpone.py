import asyncio

import pytest

import pbatch


def test_postpone():
    executed = finished = False

    def add(a, b, c=None):
        nonlocal executed, finished
        executed = True
        return a + b + c

    assert not executed

    postponement = pbatch.postpone(add, 1, 2, c=100)
    assert postponement.wait() == 103


def test_cancel():
    def to_cancel():
        return 0

    postponement = pbatch.postpone(to_cancel)
    postponement.cancel()

    with pytest.raises(asyncio.CancelledError):
        postponement.wait()


def test_exception():
    def raises_exception():
        raise ValueError("Raised exception")

    postponement = pbatch.postpone(raises_exception)

    for _ in range(2):
        with pytest.raises(ValueError) as info:
            postponement.wait()

        assert info.value.args == ("Raised exception",)
