"""
zxpy: Shell scripts made simple

To run script(s):

    zxpy script.py

To start a REPL:

    zxpy

If you haven't installed zxpy globally, you can run it by doing:

    path/to/python -m zx [...]

zxpy files can also be executed directly on a POSIX system by adding
the shebang:

    #! /use/bin/env zxpy

...to the top of your file, and executing it directly like a shell
script. Note that this requires you to have zxpy installed globally.
"""
from __future__ import annotations

import argparse
import ast
import code
import codecs
import contextlib
import inspect
import shlex
import subprocess
import sys
import traceback
from typing import Any, Generator, IO, Optional

UTF8Decoder = codecs.getincrementaldecoder("utf8")


class ZxpyArgs(argparse.Namespace):
    interactive: Optional[bool]
    filename: str


def cli() -> None:
    """
    Simple CLI interface.

    To run script(s):

        zxpy script.py

    To start a REPL:

        zxpy
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i',
        '--interactive',
        action='store_true',
        help='Run in interactive mode',
    )
    parser.add_argument('filename', help='Name of file to run', nargs='?')

    args = parser.parse_args(namespace=ZxpyArgs())

    # Remove zxpy executable from argv
    del sys.argv[0]

    if args.filename is None:
        setup_zxpy_repl()
        return

    with open(args.filename) as file:
        module = ast.parse(file.read())

        globals_dict: dict[str, Any] = {}
        try:
            run_zxpy(args.filename, module, globals_dict)
        except Exception:
            # Only catch the exception in interactive mode
            if not args.interactive:
                raise

            traceback.print_exc()

        if args.interactive:
            globals().update(globals_dict)
            install()


@contextlib.contextmanager
def create_shell_process(command: str) -> Generator[IO[bytes], None, None]:
    """Creates a shell process, yielding its stdout to read data from."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
    )
    assert process.stdout is not None
    yield process.stdout

    process.wait()
    process.stdout.close()
    if process.returncode != 0:
        raise ChildProcessError(process.returncode)


def run_shell(command: str) -> str:
    """This is indirectly run when doing ~'...'"""
    with create_shell_process(command) as stdout:
        output = stdout.read().decode()
        return output


def run_shell_print(command: str) -> None:
    """Version of `run_shell` that prints out the response instead of returning a string."""
    with create_shell_process(command) as stdout:
        decoder = UTF8Decoder()
        with open(stdout.fileno(), 'rb', closefd=False) as buff:
            for text in iter(buff.read1, b""):
                print(decoder.decode(text), end="")

            print(decoder.decode(b"", final=True), end="")


def run_shell_alternate(command: str) -> tuple[str, str, int]:
    """Like run_shell but returns 3 values: stdout, stderr and return code"""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )

    stdout_text, stderr_text = process.communicate()
    assert process.stdout is not None
    assert process.stderr is not None
    assert process.returncode is not None

    return (
        stdout_text.decode(),
        stderr_text.decode(),
        process.returncode,
    )


def run_zxpy(
    filename: str,
    module: ast.Module,
    globals_dict: dict[str, Any] | None = None,
) -> None:
    """Runs zxpy on a given file"""
    patch_shell_commands(module)
    code = compile(module, filename, mode="exec")

    if globals_dict is None:
        globals_dict = {}

    globals_dict.update(
        {
            "__name__": "__main__",
            "$run_shell": run_shell,
            "$run_shell_alternate": run_shell_alternate,
            "$run_shell_print": run_shell_print,
            "$shlex_quote": shlex.quote,
        }
    )
    exec(code, globals_dict)


def patch_shell_commands(module: ast.Module | ast.Interactive) -> None:
    """Patches the ast module to add zxpy functionality"""
    shell_runner = ShellRunner()
    shell_runner.visit(module)

    ast.fix_missing_locations(module)


def quote_fstring_args(fstring: ast.JoinedStr) -> None:
    for index, node in enumerate(fstring.values):
        if isinstance(node, ast.FormattedValue):
            # If it's marked as a raw shell string, then don't escape
            if (
                isinstance(node.format_spec, ast.JoinedStr)
                and len(node.format_spec.values) == 1
                and (
                    isinstance(node.format_spec.values[0], ast.Str)
                    and node.format_spec.values[0].s == "raw"
                    or isinstance(node.format_spec.values[0], ast.Constant)
                    and node.format_spec.values[0].value == "raw"
                )
            ):
                node.format_spec = None
                continue

            fstring.values[index] = ast.Call(
                func=ast.Name(id="$shlex_quote", ctx=ast.Load()),
                args=[node],
                keywords=[],
            )


class ShellRunner(ast.NodeTransformer):
    """Replaces the ~'...' syntax with run_shell(...)"""

    @staticmethod
    def modify_expr(
        expr: ast.expr,
        return_stderr_and_returncode: bool = False,
        print_it: bool = False,
    ) -> ast.expr:
        if (
            isinstance(expr, ast.UnaryOp)
            and isinstance(expr.op, ast.Invert)
            and isinstance(expr.operand, (ast.Str, ast.JoinedStr))
        ):
            if isinstance(expr.operand, ast.JoinedStr):
                quote_fstring_args(expr.operand)

            function_name = (
                "$run_shell_alternate"
                if return_stderr_and_returncode
                else "$run_shell_print"
                if print_it
                else "$run_shell"
            )

            return ast.Call(
                func=ast.Name(id=function_name, ctx=ast.Load()),
                args=[expr.operand],
                keywords=[],
            )

        return expr

    def visit_Expr(self, expr: ast.Expr) -> ast.Expr:
        expr.value = self.modify_expr(expr.value, print_it=True)
        super().generic_visit(expr)
        return expr

    def visit_Assign(self, assign: ast.Assign) -> ast.Assign:
        # If there's more than one target on the left, assume 3-tuple
        multiple_targets = isinstance(assign.targets[0], (ast.List, ast.Tuple))
        assign.value = self.modify_expr(
            assign.value,
            return_stderr_and_returncode=multiple_targets,
        )

        super().generic_visit(assign)
        return assign

    def visit_Call(self, call: ast.Call) -> ast.Call:
        for index, arg in enumerate(call.args):
            call.args[index] = self.modify_expr(arg)

        super().generic_visit(call)
        return call

    def visit_Attribute(self, attr: ast.Attribute) -> ast.Attribute:
        attr.value = self.modify_expr(attr.value)
        super().generic_visit(attr)
        return attr


def setup_zxpy_repl() -> None:
    """Sets up a zxpy interactive session"""
    print("zxpy shell")
    print("Python", sys.version)
    print()

    install()
    sys.exit()


class ZxpyConsole(code.InteractiveConsole):
    """Runs zxpy over"""

    def runsource(
        self,
        source: str,
        filename: str = "<console>",
        symbol: str = "single",
    ) -> bool:
        # First, check if it could be incomplete input, return True if it is.
        # This will allow it to keep taking input
        with contextlib.suppress(SyntaxError, OverflowError):
            if code.compile_command(source) == None:
                return True

        try:
            ast_obj = ast.parse(source, filename, mode=symbol)
            assert isinstance(ast_obj, ast.Interactive)
            patch_shell_commands(ast_obj)
            code_obj = compile(ast_obj, filename, mode=symbol)
        except (ValueError, SyntaxError):
            # Let the original implementation take care of incomplete input / errors
            return super().runsource(source, filename, symbol)

        self.runcode(code_obj)
        return False


def install() -> None:
    """
    Starts an interactive Python shell with zxpy features.

    Useful for setting up a zxpy session in an already running REPL.
    Simply do:

        >>> import zx; zx.install()

    and zxpy should be enabled in the REPL.
    """
    # Get locals from parent frame
    frames = inspect.getouterframes(inspect.currentframe())
    if len(frames) > 1:
        parent_frame = frames[1]
        parent_locals = parent_frame.frame.f_locals
    else:
        parent_locals = {}

    # For tab completion and arrow key support
    if sys.platform != "win32":
        import readline

        readline.parse_and_bind("tab: complete")

    zxpy_locals = {
        **parent_locals,
        "$run_shell": run_shell,
        "$run_shell_alternate": run_shell_alternate,
        "$run_shell_print": run_shell_print,
        "$shlex_quote": shlex.quote,
    }

    ZxpyConsole(locals=zxpy_locals).interact(banner="", exitmsg="")


if __name__ == "__main__":
    cli()
