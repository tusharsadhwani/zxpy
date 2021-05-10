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
import subprocess
import readline
import sys
import traceback
from typing import Union


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
        start_zxpy_repl()
        return

    for filename in filenames:
        with open(filename) as file:
            module = ast.parse(file.read())
            run_zxpy(filename, module)


def run_shell(command: str) -> str:
    """This is indirectly run when doing ~'...'"""
    output = subprocess.getoutput(command)
    return output


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
    """Wrap every top level run_shell call with print() to get output"""
    expr = expr_statement.value
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id == 'run_shell'
    ):
        new_expr = ast.Call(
            func=ast.Name(id='print', ctx=ast.Load()),
            args=[expr],
            keywords=[],
        )
        expr_statement.value = new_expr


def start_zxpy_repl() -> None:
    """
    Starts a zxpy interactive session.
    It's like the Python REPL, but supports zxpy features.
    """
    print("zxpy shell")
    print("Python", sys.version)
    print()

    # For tab completion and arrow key support
    readline.parse_and_bind("tab: complete")

    while True:
        prompt = '>>> '

        try:
            command_string = input(prompt)
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print()
            sys.exit(0)

        ast_obj = ast.parse(command_string, '<input>', 'single')
        assert isinstance(ast_obj, ast.Interactive)
        patch_shell_commands(ast_obj)

        if ast_obj is not None:
            try:
                code_obj = compile(ast_obj, '<input>', 'single')
                exec(code_obj)
            except SystemExit as e:
                sys.exit(e.code)
            except BaseException:
                traceback.print_exc()

        prompt = '... ' if ast_obj is None else '>>> '


if __name__ == '__main__':
    cli()
