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
import inspect
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
    # Remove zxpy executable from argv
    sys.argv = sys.argv[1:]

    filenames = sys.argv
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

    while True:
        char = process.stdout.read(1)
        if not char:
            break

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
        print_shell_outputs(statement)

    ast.fix_missing_locations(module)


class ShellRunner(ast.NodeTransformer):
    """Replaces the ~'...' syntax with run_shell(...)"""
    @staticmethod
    def modify_expr(expr: ast.expr) -> ast.expr:
        if (
            isinstance(expr, ast.UnaryOp)
            and isinstance(expr.op, ast.Invert)
            and isinstance(expr.operand, (ast.Str, ast.JoinedStr))
        ):
            return ast.Call(
                func=ast.Name(id='run_shell', ctx=ast.Load()),
                args=[expr.operand],
                keywords=[]
            )

        return expr

    def visit_Expr(self, expr: ast.Expr) -> ast.Expr:
        expr.value = self.modify_expr(expr.value)
        super().generic_visit(expr)
        return expr

    def visit_Assign(self, assign: ast.Assign) -> ast.Assign:
        assign.value = self.modify_expr(assign.value)
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


def print_shell_outputs(statement: ast.stmt) -> None:
    """Set print_it to True on every top level run_shell"""
    if isinstance(statement, ast.FunctionDef):
        for substatement in statement.body:
            print_shell_outputs(substatement)

    if not isinstance(statement, ast.Expr):
        return

    expr = statement.value
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

    install()


def install() -> None:
    """
    Starts an interactive shell that looks like the REPL, but with zxpy features.

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
        locals().update(parent_locals)

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
