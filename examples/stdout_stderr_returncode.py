stdout, stderr, return_code = ~'echo -n failed && exit 200'
assert stdout == 'failed'
assert return_code == 200

_, stderr, code = ~'cat .'
print(stderr, end='')
assert 'Is a directory' in stderr
assert code == 1

*_, returncode = 'exit 4'
print(returncode)
