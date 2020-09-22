import pytest

import pbatch


def _stringify_exception(e) -> str:
    if isinstance(e, Exception):
        return str(e)
    else:
        return e


def _stringify_exceptions(results):
    return list(map(_stringify_exception, results))


def test_invalid_arguments():
    with pytest.raises(TypeError):
        pbatch.pmap()

    with pytest.raises(TypeError):
        pbatch.pmap(lambda x: x)

    with pytest.raises(TypeError):
        pbatch.pmap(lambda x: x, [1, 2, 3], foo="bar")

    with pytest.raises(TypeError):
        pbatch.pmap(lambda x: x, [1, 2, 3], chunk_size=2, foo="bar")

    with pytest.raises(TypeError):
        pbatch.pmap(lambda x: x, [1, 2, 3], [4, 5, 6], foo="bar")

    with pytest.raises(TypeError):
        pbatch.pmap(lambda x: x, [1, 2, 3], [4, 5, 6], chunk_size=2, foo="bar")


@pytest.mark.parametrize("chunk_size", [None, 1, 2, 3, 4])
def test_chunk_size(chunk_size):
    def exp(x, power=2):
        return x ** power

    assert list(pbatch.pmap(exp, [1, 2, 3], chunk_size=chunk_size)) == [1, 4, 9]
    assert list(pbatch.pmap(exp, [1, 2, 3], [3, 3, 3], chunk_size=chunk_size)) == [1, 8, 27]


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
def test_pmap(items, expected):
    def square(x):
        if not isinstance(x, int):
            raise ValueError("Expected an int")
        return x ** 2

    if any(isinstance(result, Exception) for result in expected):
        expected_exceptions = [result for result in expected if isinstance(result, Exception)]

        with pytest.raises(pbatch.PMapException) as info:
            list(pbatch.pmap(square, items))

        assert str(info.value) == str(expected)
        assert repr(info.value) == repr(expected)

        assert _stringify_exceptions(info.value.results) == _stringify_exceptions(expected)
        assert all(actual.args == expected.args for actual, expected in zip(info.value.exceptions, expected_exceptions))
    else:
        assert list(pbatch.pmap(square, items)) == expected


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

    assert list(pbatch.pmap(formula, a_args, b_args, c_args)) == expected


def test_nested():
    def square(x):
        return x ** 2

    def sum_squares(numbers):
        return sum(pbatch.pmap(square, numbers))

    results = list(pbatch.pmap(sum_squares, [range(1), range(2), range(3), range(4)]))
    assert results == [0, 1, 5, 14]


def test_nested_exceptions():
    def raises_exception(_):
        raise ValueError("Nested exception")

    def map_raises_exception(items):
        return list(pbatch.pmap(raises_exception, items))

    with pytest.raises(pbatch.PMapException) as info:
        list(pbatch.pmap(map_raises_exception, [(1, 2), (3, 4)]))

    pmap_exception = info.value

    assert len(pmap_exception.results) == 2
    assert len(pmap_exception.exceptions) == 2

    assert pmap_exception.results == pmap_exception.exceptions


def test_lazy_pmap():
    seen = set()

    def square(x):
        seen.add(x)
        return x ** 2

    lazy_results = pbatch.pmap(square, [1, 2, 3, 4])
    assert seen == set()

    assert next(lazy_results) == 1
    assert seen == {1, 2, 3, 4}

    assert next(lazy_results) == 4
    assert seen == {1, 2, 3, 4}

    assert next(lazy_results) == 9
    assert seen == {1, 2, 3, 4}

    assert next(lazy_results) == 16
    assert seen == {1, 2, 3, 4}


def test_lazy_pmap_chunked():
    seen = set()

    def square(x):
        seen.add(x)
        return x ** 2

    lazy_results = pbatch.pmap(square, [1, 2, 3, 4], chunk_size=2)
    assert seen == set()

    assert next(lazy_results) == 1
    assert seen == {1, 2}

    assert next(lazy_results) == 4
    assert seen == {1, 2}

    assert next(lazy_results) == 9
    assert seen == {1, 2, 3, 4}

    assert next(lazy_results) == 16
    assert seen == {1, 2, 3, 4}


def test_exception_in_second_chunk():
    seen = set()

    def square(x):
        seen.add(x)
        if x == 3:
            raise ValueError("Number is 3")
        return x ** 2

    with pytest.raises(pbatch.PMapException) as info:
        results = list(pbatch.pmap(square, [1, 2, 3, 4], chunk_size=2))

    results = info.value.results
    exceptions = info.value.exceptions

    assert len(results) == 2
    assert exceptions[0] == results[0]
    assert results[0].args == ("Number is 3",)
    assert results[1] == 16

    assert seen == {1, 2, 3, 4}


def test_lazy_pmap_exception():
    seen = set()

    def square(x):
        seen.add(x)
        if x % 2 == 0:
            raise ValueError("Found even number")

        return x ** 2

    with pytest.raises(pbatch.PMapException) as info:
        list(pbatch.pmap(square, [1, 2, 3, 4], chunk_size=2))

    results = info.value.results
    exceptions = info.value.exceptions

    assert len(results) == 2
    assert len(exceptions) == 1

    assert results[0] == 1
    assert isinstance(results[1], ValueError) and results[1].args == ("Found even number",)
    assert exceptions[0] == results[1]

    assert seen == {1, 2}


def test_pmap_on_dict_keys_values():
    def stringify(key, value):
        return f"{key}: {value}"

    data = {"a": 1, "b": 2, "c": 3}
    assert list(pbatch.pmap(stringify, data.keys(), data.values())) == ["a: 1", "b: 2", "c: 3"]
