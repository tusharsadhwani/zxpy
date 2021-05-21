#! /usr/bin/env zxpy
~'echo Hello world!'


def print_file_count():
    file_count = ~'ls -1 | wc -l'

    ~"echo -n 'file count is: '"
    print(file_count)


print_file_count()
