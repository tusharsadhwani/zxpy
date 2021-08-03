#! /usr/bin/env zxpy

arg = "test string with spaces"

output = ~f"python -c 'import sys; print(sys.argv[1])' {arg}"
assert output.rstrip('\n') == arg

cmd = 'yes zxpy | head -5'
val = ~f'{cmd:raw}'
assert val == 'zxpy\n' * 5
