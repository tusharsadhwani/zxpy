# zxpy

Shell scripts made simple

> Note: Work in progress. Most of the functionality will be added pretty soon

## Installation

`pip install zxpy`

## Example

Make a file `example.zxpy`

```python
#! /usr/bin/env zxpy
~'echo Hello world!'

file_count = ~'ls -1 | wc -l'

~"echo 'file count is:'"
print(file_count)
```

Output:

```bash
$ ./example.zxpy
Hello world!
File count is:
9
```
