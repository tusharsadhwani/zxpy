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
