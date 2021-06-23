import ast
import os
import pytest

import zx


@pytest.mark.parametrize(
    ('command', 'output'),
    (
        ('echo hello world', 'hello world'),
        ('ls | tail -6 | wc -l', '6'),
        ("find . -maxdepth 1 -name '*\\.py' | grep -v test | wc -l", '3'),
        ("cat /etc/shadow 2> /dev/null; echo $?", '1'),
    )
)
def test_shell_output(command: str, output: str) -> None:
    assert zx.run_shell(command).rstrip('\r\n') == output


def test_files() -> None:
    test_files = [
        './tests/test_files/yeses.py',
    ]

    for filepath in test_files:
        filename = os.path.basename(filepath)

        with open(filepath) as file:
            module = ast.parse(file.read())
            zx.run_zxpy(filename, module)
