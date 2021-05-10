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
import ast
import code
import readline
import subprocess
import sys
import traceback
from typing import Optional, Union


def cli() -> None:
    """
    Simple CLI interface.

    To run script(s):

        zxpy script.py

    To start a REPL:

        zxpy
    """
    filenames = sys.argv[1:]

    if not filenames:
        setup_zxpy_repl()
        return

    for filename in filenames:
        with open(filename) as file:
            module = ast.parse(file.read())
            run_zxpy(filename, module)


def run_shell(command: str, print_it: bool = False) -> Optional[str]:
    """This is indirectly run when doing ~'...'"""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )
    assert process.stdout is not None

    if not print_it:
        return process.stdout.read().decode()

    while char := process.stdout.read(1):
        if print_it:
            sys.stdout.buffer.write(char)
            sys.stdout.flush()

    return None


def run_zxpy(filename: str, module: ast.Module) -> None:
    """Runs zxpy on a given file"""
    patch_shell_commands(module)
    exec(compile(module, filename, mode='exec'))


def patch_shell_commands(module: Union[ast.Module, ast.Interactive]) -> None:
    """Patches the ast module to add zxpy functionality"""
    shell_runner = ShellRunner()
    shell_runner.visit(module)

    for statement in module.body:
        if not isinstance(statement, ast.Expr):
            continue
        print_shell_outputs(statement)

    ast.fix_missing_locations(module)


class ShellRunner(ast.NodeTransformer):
    """Replaces the ~'...' syntax with run_shell(...)"""
    @staticmethod
    def modify_expr(expr: ast.Expr) -> ast.Expr:
        if (
            isinstance(expr.value, ast.UnaryOp)
            and isinstance(expr.value.op, ast.Invert)
            and isinstance(expr.value.operand, (ast.Str, ast.JoinedStr))
        ):
            expr.value = ast.Call(
                func=ast.Name(id='run_shell', ctx=ast.Load()),
                args=[expr.value.operand],
                keywords=[]
            )

        return expr

    def visit_Expr(self, expr: ast.Expr) -> ast.Expr:
        return self.modify_expr(expr)

    def visit_Assign(self, assign: ast.Assign) -> ast.Assign:
        if isinstance(assign.value, ast.expr):
            expr = ast.Expr(assign.value)
            new_expr = self.modify_expr(expr)
            assign.value = new_expr.value

        return assign


def print_shell_outputs(expr_statement: ast.Expr) -> None:
    """Set print_it to True on every top level run_shell"""
    expr = expr_statement.value
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id == 'run_shell'
    ):
        expr.keywords = [
            ast.keyword(
                arg='print_it',
                value=ast.Constant(value=True),
            )
        ]


def setup_zxpy_repl() -> None:
    """
    Sets up a zxpy interactive session.
    """
    print("zxpy shell")
    print("Python", sys.version)
    print()

    start()


def start() -> None:
    """
    It's like the Python REPL, but supports zxpy features.
    Starts the zxpy REPL.

    Useful for setting up a zxpy session in an already running REPL.
    Simply do:

        >>> import zx; zx.start()

    and zxpy should be enabled in the REPL.
    """
    # For tab completion and arrow key support
    readline.parse_and_bind("tab: complete")

    command = ''
    continued_command = False
    while True:
        try:
            if continued_command:
                command += '\n'
            else:
                command = ''

            prompt = '... ' if continued_command else '>>> '
            new_input = input(prompt)

            if new_input != '':
                command += new_input
            else:
                continued_command = False

        except KeyboardInterrupt:
            print()
            continue

        except EOFError:
            print()
            sys.exit(0)

        if continued_command:
            continue

        try:
            ast_obj = ast.parse(command, '<input>', 'single')
        except SyntaxError:
            try:
                code_obj = code.compile_command(command)
                if code_obj is None:
                    continued_command = True
                    continue

            except BaseException:
                traceback.print_exc()
                continue

        assert isinstance(ast_obj, ast.Interactive)
        patch_shell_commands(ast_obj)

        try:
            code_obj = compile(ast_obj, '<input>', 'single')
            assert code_obj is not None
            exec(code_obj)

        except SystemExit as e:
            sys.exit(e.code)

        except BaseException:
            traceback.print_exc()


if __name__ == '__main__':
    cli()
