#! /usr/bin/env zxpy
~'echo Hello world!'

file_count = ~'ls -1 | wc -l'

~"echo 'file count is:'"
print(file_count)
