_, _, return_code = ~"false"
assert return_code == 1

exit_code = 123
*_, return_code = ~f"exit {exit_code}"
assert return_code == exit_code

[_, _, return_code] = ~'echo hi'
assert return_code == 0
