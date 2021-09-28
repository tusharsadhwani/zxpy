import ast
import contextlib
import io
import os
from contextlib import redirect_stdout

import pytest
import zx


@pytest.mark.parametrize(
    ("command", "output"),
    (
        ("echo hello world", "hello world"),
        ("ls | tail -6 | wc -l", "6"),
        ("find . -maxdepth 1 -name '*\\.py' | grep -v test | wc -l", "3"),
        ("cat /etc/shadow 2> /dev/null; echo $?", "1"),
    ),
)
def test_shell_output(command: str, output: str) -> None:
    assert zx.run_shell(command).rstrip("\r\n") == output


@pytest.mark.parametrize(
    ("command", "stdout", "stderr", "return_code"),
    (
        ("echo hello world", "hello world\n", "", 0),
        ("echo -n failed && exit 200", "failed", "", 200),
        ("cat .", "", "cat: .: Is a directory\n", 1),
    ),
)
def test_stdout_stderr_returncode(
    command: str,
    stdout: str,
    stderr: str,
    return_code: int,
) -> None:
    assert zx.run_shell_alternate(command) == (stdout, stderr, return_code)


@pytest.mark.parametrize(
    ("filepath"),
    (
        "./tests/test_files/yeses.py",
        "./tests/test_files/returncode.py",
        "./tests/test_files/quoting.py",
    ),
)
def test_files(filepath) -> None:
    filename = os.path.basename(filepath)

    with open(filepath) as file:
        module = ast.parse(file.read())
        zx.run_zxpy(filename, module)


def test_prints() -> None:
    filepath = "./tests/test_files/prints.py"
    filename = os.path.basename(filepath)

    with open(filepath) as file:
        with redirect_stdout(io.TextIOWrapper(io.BytesIO())) as output:
            module = ast.parse(file.read())
            zx.run_zxpy(filename, module)

        expected = (
            b"hi\n"
            b"0123456789\n"
            b"hello, this is main.\n"
            b"var='abc'\n"
            b"var='xyz'\n"
        )
        assert output.buffer.getvalue() == expected
