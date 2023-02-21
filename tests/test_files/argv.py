import sys

assert len(sys.argv) == 3
assert sys.argv[1] == "foobar"
assert sys.argv[2] == "baz"

out = ~"echo $1 and $2"
assert out == "foobar and baz\n"
