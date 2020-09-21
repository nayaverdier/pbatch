import itertools
from types import GeneratorType

import pytest

import pbatch

PARAMETERS = "items,chunk_size,expected_list"
EXPECTED_PARTITIONS = [
    ([], None, []),
    ([1], None, [[1]]),
    ([1, 2, 3], None, [[1, 2, 3]]),
    ([], 1, []),
    ([1], 1, [[1]]),
    ([1, 2, 3], 1, [[1], [2], [3]]),
    (range(15), 4, [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14]]),
    (range(16), 8, [[0, 1, 2, 3, 4, 5, 6, 7], [8, 9, 10, 11, 12, 13, 14, 15]]),
    (["a", "b", "c"], 10, [["a", "b", "c"]]),
    ([(1, 2, 3), (4, 5, 6), (7, 8, 9)], 2, [[(1, 2, 3), (4, 5, 6)], [(7, 8, 9)]]),
    ([{"a": 1}, {"b": 2}], 3, [[{"a": 1}, {"b": 2}]]),
]


@pytest.mark.parametrize("args", [(), ([1, 2, 3]), (2,), (1, 2, 3)])
def test_invalid_arguments(args):
    with pytest.raises(TypeError):
        pbatch.partition(*args)


@pytest.mark.parametrize("chunk_size", ["not an int", 1.25, 0, -1, -10])
def test_non_int_chunk_size(chunk_size):
    with pytest.raises(AssertionError) as info:
        list(pbatch.partition([], chunk_size))

    assert str(info.value) == "Chunk size must be a positive int (or None)"


@pytest.mark.parametrize(PARAMETERS, EXPECTED_PARTITIONS)
def test_generator_returned(items, chunk_size, expected_list):
    partitions = pbatch.partition(items, chunk_size)
    assert isinstance(partitions, GeneratorType)

    if expected_list:
        assert next(partitions) == expected_list[0]

        for actual, expected in zip(partitions, expected_list[1:]):
            assert actual == expected
    else:
        assert list(partitions) == []


@pytest.mark.parametrize(PARAMETERS, EXPECTED_PARTITIONS)
def test_partitions(items, chunk_size, expected_list):
    assert list(pbatch.partition(items, chunk_size)) == expected_list


@pytest.mark.parametrize(PARAMETERS, EXPECTED_PARTITIONS)
def test_chunk_size_kwarg(items, chunk_size, expected_list):
    assert list(pbatch.partition(items, chunk_size=chunk_size)) == expected_list


@pytest.mark.parametrize(PARAMETERS, EXPECTED_PARTITIONS)
def test_items_and_chunk_size_kwargs(items, chunk_size, expected_list):
    assert list(pbatch.partition(items=items, chunk_size=chunk_size)) == expected_list


@pytest.mark.parametrize(PARAMETERS, EXPECTED_PARTITIONS)
def test_tuple_items(items, chunk_size, expected_list):
    assert (
        list(pbatch.partition(items=tuple(items), chunk_size=chunk_size))
        == expected_list
    )


@pytest.mark.parametrize(PARAMETERS, EXPECTED_PARTITIONS)
def test_set_items(items, chunk_size, expected_list):
    # cannot use dict items in a set (not hashable)
    if isinstance(next(iter(items), None), dict):
        return

    partitions = pbatch.partition(items=set(items), chunk_size=chunk_size)
    assert sorted(itertools.chain(*partitions)) == sorted(
        itertools.chain(*expected_list)
    )


@pytest.mark.parametrize(PARAMETERS, EXPECTED_PARTITIONS)
def test_iter_items(items, chunk_size, expected_list):
    assert (
        list(pbatch.partition(items=iter(items), chunk_size=chunk_size))
        == expected_list
    )


@pytest.mark.parametrize(PARAMETERS, EXPECTED_PARTITIONS)
def test_generator_items(items, chunk_size, expected_list):
    def items_generator():
        yield from items

    assert (
        list(pbatch.partition(items=items_generator(), chunk_size=chunk_size))
        == expected_list
    )


def test_consumes_iterator():
    iterator = iter([1, 2, 3, 4])
    partitions = pbatch.partition(iterator, 2)

    assert next(partitions) == [1, 2]
    assert list(iterator) == [3, 4]
    assert list(partitions) == []
