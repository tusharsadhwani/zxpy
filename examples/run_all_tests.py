#! /usr/bin/env zxpy
test_files = (~"find -name '*_test\.py'").splitlines()

for filename in test_files:
    try:
        print(f'Running {filename:.<50}', end='')
        output = ~f'python {filename}'  # variables in your shell commands :D
        assert output == ''
        print('Test passed!')
    except:
        print(f'Test failed.')
