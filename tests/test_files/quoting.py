#! /usr/bin/env zxpy

arg = "test string with spaces"

output = ~f"python -c 'import sys; print(sys.argv[1])' {arg}"
assert output.rstrip('\n') == arg
