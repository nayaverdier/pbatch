import asyncio
import itertools
from typing import Any, Callable, Coroutine, Iterable, List, Optional, Tuple, TypeVar

OutputType = TypeVar("OutputType")


def partition(items: Iterable[OutputType], chunk_size: Optional[int]) -> Iterable[List[OutputType]]:
    """Partition an iterable of items into lists of at most the specified
    chunk size

    :param items: The iterable of items to partition
    :chunk_size: The maximum size for each part. The final part may be
        smaller if the chunk size does not divide the number of total
        items. If set to None, all items will be in a single part.

    :return: A generator yielding lists of items
    """

    positive_int = isinstance(chunk_size, int) and chunk_size > 0
    assert chunk_size is None or positive_int, "Chunk size must be a positive int (or None)"

    iterator = iter(items)
    part = list(itertools.islice(iterator, chunk_size))
    while part:
        yield part
        part = list(itertools.islice(iterator, chunk_size))


class Postpone:
    """Runs the provided function (with arguments) in the background, not
    blocking until Postpone.wait() is called.

    Has attributes `loop` and `task` containing the asyncio event loop
    and Task objects for the postponed execution
    """

    def __init__(self, f: Callable[..., OutputType], args, kwargs):
        self.loop = asyncio.new_event_loop()
        self.task = _run_in_background(f, self.loop, args, kwargs)

    def cancel(self):
        """Cancels the task, even if it is not yet finished"""

        try:
            self.task.cancel()
        finally:
            self.loop.close()

    def wait(self) -> OutputType:
        """Waits until the postponed task is complete, and then returns its
        result. If an exception was raised within the task, it will be
        re-raised from this function.

        :return: The result of the task's execution

        :raise: Any exception that the task may raise during execution
        """

        if not self.loop.is_closed():
            self.loop.run_until_complete(self.task)

        try:
            return self.task.result()  # type: ignore
        finally:
            self.loop.close()


def postpone(_pbatch_f: Callable[..., OutputType], *args, **kwargs):
    """Runs the provided function (with arguments) in the background, not
    blocking until Postpone.wait() is called.

    :param _pbatch_f: The function to postpone
    :param *args: Positional arguments to pass to the function
    :param **kwargs: Keyword arguments to pass to the function

    :return: A Postpone instance with `.wait()` functionality
    """

    return Postpone(_pbatch_f, args, kwargs)


class PMapException(Exception):
    """An exception to hold results and exceptions from a pmap execution,
    when exceptions were raised within tasks.

    :param results: A list of all results from the pmap, in
        order. Includes exception instances in place of results if an
        exception was raised (indistinguishable from the mapped
        function returning an exception)
    :param exceptions: A list of all exceptions that were raised
    """

    def __init__(self, results: List[Any], exceptions: List[Exception]):
        self.results = results
        self.exceptions = exceptions

    def __str__(self):
        return str(self.results)

    def __repr__(self):
        return repr(self.results)


def pmap(
    f: Callable[..., OutputType],
    iterable: Iterable,
    *iterables: Iterable,
    chunk_size: int = None,
) -> List[OutputType]:
    """Maps a function over the provided arguments, in parallel. If
    multiple iterables are provided, the function must accept that
    many arguments and will be passed a corresponding value from each
    iterable.

    If chunk_size is provided, it is used as the limit to the number
    of concurrent executions.

    :param f: The function to execute each item with
    :param iterable: The first argument to pass to each function
        execution.
    :param iterables: Additional arguments to pass to each function
        execution.
    :param chunk_size: (optional) The maximum number of items to run
        at any given time. If None, all items will be executed at the
        same time. Defaults to None

    :return: A list of return values for each function call (in the
        same order as the items coming in)

    :raises: PMapException if any exceptions were raised in the mapped
        function
    """

    partitions = partition(zip(iterable, *iterables), chunk_size)

    return list(_run_pmap(f, partitions))


def _make_async_mapper(f: Callable[..., OutputType]):
    async def async_f(loop, args) -> OutputType:
        return await _run_in_background(f, loop, args, {})

    async def async_mapper(loop, items: List[Tuple]) -> List[OutputType]:
        tasks = [loop.create_task(async_f(loop, item)) for item in items]

        # .wait requires at least one task
        if tasks:
            await asyncio.wait(tasks, loop=loop)

        results = []
        exceptions = []
        for task in tasks:
            exception = task.exception()
            if exception is None:
                results.append(task.result())
            else:
                results.append(exception)
                exceptions.append(exception)

        if exceptions:
            raise PMapException(results, exceptions)

        return results

    return async_mapper


def _run_pmap(
    f: Callable[..., OutputType],
    partitions: Iterable[List[Tuple]],
) -> Iterable[OutputType]:
    async_mapper = _make_async_mapper(f)
    loop = asyncio.new_event_loop()

    try:
        for partition in partitions:
            yield from loop.run_until_complete(async_mapper(loop, partition))
    finally:
        loop.close()


def _run_in_background(f: Callable[..., OutputType], loop, args, kwargs) -> Coroutine[Any, Any, OutputType]:
    return loop.run_in_executor(None, lambda: f(*args, **kwargs))
