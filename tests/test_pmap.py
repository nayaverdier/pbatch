import pytest

import pbatch


def _stringify_exception(e) -> str:
    if isinstance(e, Exception):
        return str(e)
    else:
        return e


def _stringify_exceptions(results):
    return list(map(_stringify_exception, results))


@pytest.mark.parametrize("args", [(), (print,)])
def test_invalid_arguments(args):
    with pytest.raises(TypeError):
        pbatch.pmap(*args)


@pytest.mark.parametrize("chunk_size", [None, 1, 2, 3, 4])
def test_chunk_size(chunk_size):
    def exp(x, power=2):
        return x ** power

    assert pbatch.pmap(exp, [1, 2, 3], chunk_size=chunk_size) == [1, 4, 9]
    assert pbatch.pmap(exp, [1, 2, 3], [3, 3, 3], chunk_size=chunk_size) == [1, 8, 27]


@pytest.mark.parametrize(
    "items,expected",
    [
        ([], []),
        ([0], [0]),
        ([1, 2, 3], [1, 4, 9]),
        (range(10), [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]),
        ((1, 2, 3), [1, 4, 9]),
        (["not an int"], [ValueError("Expected an int")]),
        ([1, 2, "not an int"], [1, 4, ValueError("Expected an int")]),
    ],
)
def test_square_function(items, expected):
    def square(x):
        if not isinstance(x, int):
            raise ValueError("Expected an int")
        return x ** 2

    if any(isinstance(result, Exception) for result in expected):
        expected_exceptions = [
            result for result in expected if isinstance(result, Exception)
        ]

        with pytest.raises(pbatch.PMapException) as info:
            pbatch.pmap(square, items)

        assert str(info.value) == str(expected)
        assert repr(info.value) == repr(expected)

        assert _stringify_exceptions(info.value.results) == _stringify_exceptions(
            expected
        )
        assert all(
            actual.args == expected.args
            for actual, expected in zip(info.value.exceptions, expected_exceptions)
        )
    else:
        assert pbatch.pmap(square, items) == expected


@pytest.mark.parametrize(
    "a_args,b_args,c_args,expected",
    [
        ([], [], [], []),
        ([], range(1000), range(100), []),
        ([1], range(1000), range(100), [1]),
        (
            range(0, 10),
            range(0, 100, 10),
            range(0, 1000, 100),
            [0, 1001, 4002, 9003, 16004, 25005, 36006, 49007, 64008, 81009],
        ),
    ],
)
def test_multi_arity(a_args, b_args, c_args, expected):
    def formula(a, b, c):
        return a + b * c

    assert pbatch.pmap(formula, a_args, b_args, c_args) == expected


def test_nested():
    def square(x):
        return x ** 2

    def sum_squares(numbers):
        return sum(pbatch.pmap(square, numbers))

    results = pbatch.pmap(sum_squares, [range(1), range(2), range(3), range(4)])
    assert results == [0, 1, 5, 14]


def test_nested_exceptions():
    def raises_exception(_):
        raise ValueError("Nested exception")

    def map_raises_exception(items):
        return pbatch.pmap(raises_exception, items)

    with pytest.raises(pbatch.PMapException) as info:
        pbatch.pmap(map_raises_exception, [(1, 2), (3, 4)])

    pmap_exception = info.value

    assert len(pmap_exception.results) == 2
    assert len(pmap_exception.exceptions) == 2

    assert pmap_exception.results == pmap_exception.exceptions
