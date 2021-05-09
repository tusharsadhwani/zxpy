"""zxpy: Shell scripts made simple"""
import ast
import subprocess
import sys


def cli() -> None:
    """
    Simple CLI interface.

    Example:

        zxpy script.py
    """
    filenames = sys.argv[1:]
    for filename in filenames:
        with open(filename) as file:
            module = ast.parse(file.read())
            run_zxpy(filename, module)


def run_shell(command: str) -> str:
    output = subprocess.getoutput(command)
    return output


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


def run_zxpy(filename: str, module: ast.Module) -> None:
    shell_runner = ShellRunner()
    shell_runner.visit(module)

    for statement in module.body:
        if not isinstance(statement, ast.Expr):
            continue

        print_shell_outputs(statement)

    ast.fix_missing_locations(module)

    exec(compile(module, filename, mode='exec'))


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
