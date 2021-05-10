# zxpy

Shell scripts made simple 🐚

Inspired by Google's [zx](https://github.com/google/zx), but made much simpler and more accessible using Python.

## Installation

`pip install zxpy`

## Example

Make a file `script.py` (The name and extension can be anything):

```python
#! /usr/bin/env zxpy
~'echo Hello world!'

file_count = ~'ls -1 | wc -l'
print("file count is:", file_count)
```

And then run it:

```bash
$ chmod +x ./script.py

$ ./script.py
Hello world!
file count is: 3
```

> Run `>>> help('zxpy')` in Python REPL to find out more ways to use zxpy.

A more involved example: [run_all_tests.py](./examples/run_all_tests.py)

```python
#! /usr/bin/env zxpy
test_files = ~"find -name '*_test\.py'"

for filename in test_files.splitlines():
    try:
        print(f'Running {filename:.<50}', end='')
        output = ~f'python {filename}'  # variables in your shell commands :D
        assert output == ''
        print('Test passed!')
    except:
        print(f'Test failed.')
```

Output:

```bash
$ ./run_all_tests.py
Running ./tests/python_version_test.py....................Test failed.
Running ./tests/platform_test.py..........................Test passed!
Running ./tests/imports_test.py...........................Test passed!
```

Examples are all in the [examples folder](./examples).

## Interactive mode

```pycon
$ zxpy
zxpy shell
Python 3.8.5 (default, Jan 27 2021, 15:41:15)
[GCC 9.3.0]

>>> ~"ls | grep '\.py'"
__main__.py
setup.py
zx.py
>>>
```

> Also works with `path/to/python -m zx`

It can also be used to start a zxpy session in an already running REPL.
Simply do:

```pycon
>>> import zx; zx.start()
```

and zxpy should be enabled in the existing session.
