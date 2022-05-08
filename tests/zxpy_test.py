import ast
import io
import os
import subprocess
import sys
from textwrap import dedent

import pytest
import zx


@pytest.mark.parametrize(
    ("command", "output"),
    (
        ("echo hello world", "hello world"),
        ("ls | tail -6 | wc -l", "6"),
        ("find . -maxdepth 1 -name '*\\.py' | grep -v test | wc -l", "2"),
        ("cat /etc/shadow 2> /dev/null; echo $?", "1"),
    ),
)
def test_shell_output(command: str, output: str) -> None:
    assert zx.run_shell(command).rstrip("\r\n").strip(" ") == output


@pytest.mark.parametrize(
    ("command", "stdout", "stderr", "return_code"),
    (
        ("echo hello world", "hello world\n", "", 0),
        ("echo failed && exit 200", "failed\n", "", 200),
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
def test_files(filepath: str) -> None:
    filename = os.path.basename(filepath)

    with open(filepath) as file:
        module = ast.parse(file.read())
        zx.run_zxpy(filename, module)


def test_prints(capsys: pytest.CaptureFixture[str]) -> None:
    filepath = "./tests/test_files/prints.py"
    filename = os.path.basename(filepath)

    with open(filepath) as file:
        module = ast.parse(file.read())
        zx.run_zxpy(filename, module)

        expected = dedent(
            """\
            hi
            1
            1 2
            1 2 3
            1 2 3 4
            done
            hello, this is main.
            var='abc'
            var='xyz'
            """
        )
        assert capsys.readouterr().out == expected


def test_argv() -> None:
    test_file = "./tests/test_files/argv.py"
    subprocess.run(["zxpy", test_file])


def test_raise() -> None:
    with pytest.raises(ChildProcessError) as exc:
        zx.run_shell("exit 1")

    assert exc.value.args == (1,)


def test_interactive(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    process = subprocess.Popen(
        ["zxpy", "-i"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout, stderr = process.communicate(input=b"~'echo hi'\nprint(10)\n")
    assert stderr == b''
    outlines = [line for line in stdout.decode().splitlines() if line.startswith('>>>')]
    assert outlines == [">>> hi", ">>> 10", ">>> "]
