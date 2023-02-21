import ast
import os
import subprocess
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
    returncode = subprocess.check_call(["zxpy", test_file, "--", "foobar", "baz"])
    assert returncode == 0


def test_raise() -> None:
    with pytest.raises(ChildProcessError) as exc:
        zx.run_shell("exit 1")

    assert exc.value.args == (1,)


def test_interactive() -> None:
    process = subprocess.Popen(
        ["zxpy", "-i"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    code = dedent(
        """\
        ~'echo hi'
        print(10)
        def f(n):
            if n < 2:
                return 1
            return f(n-1) + f(n-2)

        print(f(5))
        """
    )

    stdout, stderr = process.communicate(input=code.encode())
    assert stderr == b'\n'
    outlines = [line for line in stdout.decode().splitlines() if line.startswith('>>>')]
    assert outlines == [">>> hi", ">>> 10", ">>> ... ... ... ... >>> 8", ">>> "]


@pytest.mark.parametrize(
    ("input", "index", "output"),
    (
        ("echo 'hello world' hi", 0, False),
        ("echo 'hello world' hi", 4, False),
        ("echo 'hello world' hi", 5, True),
        ("echo 'hello world' hi", 6, True),
        ("echo 'hello world' hi", 16, True),
        ("echo 'hello world' hi", 17, True),
        ("echo 'hello world' hi", 18, False),
        ("echo 'hello world' hi", 21, False),
        ('abc "def\'ghi" jkl \'mnop\'', 5, False),
        ('abc "def\'ghi" jkl \'mnop\'', 8, False),
        ('abc "def\'ghi" jkl \'mnop\'', 10, False),
        ('abc "def\'ghi" jkl \'mnop\'', 14, False),
        ('abc "def\'ghi" jkl \'mnop\'', 17, False),
        ('abc "def\'ghi" jkl \'mnop\'', 18, True),
        ('abc "def\'ghi" jkl \'mnop\'', 21, True),
        ("'a'  'b'  c 'de' 'fg' h", 1, True),
        ("'a'  'b'  c 'de' 'fg' h", 3, False),
        ("'a'  'b'  c 'de' 'fg' h", 6, True),
        ("'a'  'b'  c 'de' 'fg' h", 10, False),
        ("'a'  'b'  c 'de' 'fg' h", 14, True),
        ("'a'  'b'  c 'de' 'fg' h", 16, False),
        ("'a'  'b'  c 'de' 'fg' h", 19, True),
        ("'a'  'b'  c 'de' 'fg' h", 22, False),
        ("a \"b'c'd'e\" '\"' '\"abc'", 1, False),
        ("a \"b'c'd'e\" '\"' '\"abc'", 2, False),
        ("a \"b'c'd'e\" '\"' '\"abc'", 4, False),
        ("a \"b'c'd'e\" '\"' '\"abc'", 6, False),
        ("a \"b'c'd'e\" '\"' '\"abc'", 8, False),
        ("a \"b'c'd'e\" '\"' '\"abc'", 10, False),
        ("a \"b'c'd'e\" '\"' '\"abc'", 12, True),
        ("a \"b'c'd'e\" '\"' '\"abc'", 13, True),
        ("a \"b'c'd'e\" '\"' '\"abc'", 14, True),
        ("a \"b'c'd'e\" '\"' '\"abc'", 15, False),
        ("a \"b'c'd'e\" '\"' '\"abc'", 16, True),
        ("a \"b'c'd'e\" '\"' '\"abc'", 17, True),
        ("a \"b'c'd'e\" '\"' '\"abc'", 18, True),
        ("a \"b'c'd'e\" '\"' '\"abc'", 20, True),
    ),
)
def test_is_inside_single_quotes(input, index, output) -> None:
    assert zx.is_inside_single_quotes(input, index) == output


def test_shell_injection():
    """Test injecting commands or shell args like `$0` into shell strings."""
    file = "./tests/test_files/injection.py"
    output = subprocess.check_output(["zxpy", file, "--", "abc"]).decode()
    assert output == (
        "True\n"  # uname -p worked as a string
        "127\n"  # uname -p inside f-string got quoted
    )
    # TODO: $1 injection test
