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
