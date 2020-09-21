# pbatch

Parallel batch processing on top of regular python functions

## Installation

Requires python 3.7+

```bash
pip install pbatch
```

## Usage

### `pbatch.pmap`

Similar to built-in `map`, but executes the function in
parallel. Number of concurrent executions can be limited through a
`chunk_size` keyword argument.

```python
import time
import pbatch

def long_square(x):
    time.sleep(1)
    print(x)
    return x ** 2

list(map(long_square, [1, 2, 3]))
# 1
# 2
# 3
# => [1, 4, 9] (after 3 seconds)

list(pbatch.pmap(long_square, [1, 2, 3]))
# 1
# 2
# 3
# => [1, 4, 9] (after 1 second)

list(pbatch.pmap(long_square, [1, 2, 3], chunk_size=2))
# 1
# 2
# 3
# => [1, 4, 9] (after 2 seconds)
```

Supports multiple-arity functions exactly as `map` does:
```python
import time
import pbatch

def multiple_args(a, b, c):
    print(f"a={a}, b={b}, c={c})
    time.sleep(1)
    return c

list(map(multiple_args, [1, 2], [60, 70], [1000, 2000]))
# a=1, b=60, c=1000
# a=2, b=70, c=2000
# => [1000, 2000] (after 2 seconds)

list(pbatch.pmap(multiple_args, [1, 2], [60, 70], [1000, 2000]))
# a=1, b=60, c=1000
# a=2, b=70, c=2000
# => [1000, 2000] (after 1 second)

list(pbatch.pmap(multiple_args, [1, 2], [60, 70], [1000, 2000], chunk_size=1))
# a=1, b=60, c=1000
# a=2, b=70, c=2000
# => [1000, 2000] (after 2 second)
```

Note that if one iterable is shorter than the rest, remaining elements
in the other iterators will be ignored.

If any of the subtasks raises an exception, a `pbatch.PMapException`
will be raised:

```python
def raise_on_two(x):
    if x == 2:
        raise ValueError("Number is two")
    return x

try:
    pbatch.pmap(raise_on_two, [1, 2, 3])
except pbatch.PMapException as e:
    e.results
    # => [1, ValueError("Number is two"), 3]

    e.exceptions
    # => [ValueError("Number is two")]

    str(e)
    # => "[1, ValueError('Number is two'), 3]"

    repr(e)
    # => "[1, ValueError('Number is two'), 3]"
```

### `pbatch.postpone`

Begin execution of a function without blocking code execution (until
`.wait()` is called)

```python
import time
import pbatch

def long_function(x, power=2):
    time.sleep(1)
    return x ** power

postponement = pbatch.postpone(long_function, 3, power=3)
time.sleep(1)
result = postponement.wait()  # does not wait 1 second anymore
```

### `pbatch.partition`

Split up an iterable into fixed-sized chunks (except the final chunk
in some cases)

Returns a generator that yields lists of elements (chunks)

```python
import pbatch

partitions = list(pbatch.partition([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], chunk_size=4))
# => [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10]]
```

Chunks are lazily generated:
```python
def print_return(x):
    print(x)
    return x

next(pbatch.partition(map(print_return, range(10)), 4))
# 0
# 1
# 2
# 3
# => [0, 1, 2, 3]
```

## Development

Clone the repo, then from the project directory:

```bash
python3.7 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

To run tests (and show coverage):
```bash
tox -p

# to skip performances test (speeds up testing)
tox -p -- -m "not performance"
```

Make sure to run `pre-commit` before any commits. `pre-commit install`
will automatically do this before committing.
