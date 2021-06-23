import pytest

import zx


@pytest.mark.parametrize(
    ('command', 'output'),
    (
        ('echo hello world', 'hello world'),
    )
)
def test_shell_output(command: str, output: str) -> None:
    assert zx.run_shell(command).rstrip('\r\n') == output
