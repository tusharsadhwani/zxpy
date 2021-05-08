# zxpy

Shell scripts made simple

## Installation

`pip install zxpy`

## Example

Make a file `script.py` (The name and extension can be anything):

```python
#! /usr/bin/env zxpy
~'echo Hello world!'

file_count = ~'ls -1 | wc -l'

~"echo 'file count is:'"
print(file_count)
```

Output:

```bash
$ chmod +x ./script.py

$ ./script.py
Hello world!
File count is:
3
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
    except AssertionError:
        print(f'Test failed.')
    except ModuleNotFoundError:
        print(f'Unable to import file')
```

Output:

```bash
$ ./run_all_tests.py
Running ./tests/python_version_test.py....................Test failed.
Running ./tests/platform_test.py..........................Test passed!
Running ./tests/imports_test.py...........................Test passed!
```

Examples are all in the [examples folder](./examples).
