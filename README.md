# zxpy

Shell scripts made simple

> Note: Work in progress. Most of the functionality will be added pretty soon

## Installation

`pip install zxpy`

## Example

Make a file `example.zxpy` (The extension can be anything)

```python
#! /usr/bin/env zxpy
~'echo Hello world!'

file_count = ~'ls -1 | wc -l'

~"echo 'file count is:'"
print(file_count)
```

Output:

```bash
$ chmod +x ./example.zxpy

$ ./example.zxpy
Hello world!
File count is:
9
```
