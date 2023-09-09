x = ~"uname -p"
print(x in ("arm\n", "unknown\n", "x86_64\n"))

command = "uname -p"
_, _, rc = ~f"{command}"  # This doesn't work
print(rc)

print(~"echo $1", end='')
print(~'echo "$1"', end='')
print(~"echo '$1'", end='')

argument = "$1"
quoted_argument = '"$1"'
print(~f"echo {argument}", end='')
print(~f"echo {quoted_argument}", end='')
