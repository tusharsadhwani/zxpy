x = ~"uname -p"
print(x in ("arm\n", "x86_64\n"))

command = "uname -p"
_, _, rc = ~f"{command}"  # This doesn't work
print(rc)
