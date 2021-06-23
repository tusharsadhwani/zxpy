#! /usr/bin/env zxpy
file_count = int(~"ls | wc -l")
yeses = (~f'yes | head -{file_count}').splitlines()
assert len(yeses) == file_count
