"""zxpy: Shell scripts made simple"""
import ast
import subprocess
import sys


def cli() -> None:
    filenames = sys.argv[1:]
    for filename in filenames:
        with open(filename) as file:
            module = ast.parse(file.read())
            run_zxpy(filename, module)


def run_shell(command: str) -> str:
    output = subprocess.getoutput(command)
    return output


class BashCaller(ast.NodeTransformer):
    @staticmethod
    def modify_expr(expr: ast.Expr) -> ast.Expr:
        if not isinstance(expr.value, ast.UnaryOp):
            return expr

        if not isinstance(expr.value.op, ast.Invert):
            return expr

        if not isinstance(expr.value.operand, (ast.Str, ast.JoinedStr)):
            return expr

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
    transformer = BashCaller()
    transformer.visit(module)

    for statement in module.body:
        if isinstance(statement, ast.Expr):
            expr = statement.value
            if not isinstance(expr, ast.Call):
                continue

            if not isinstance(expr.func, ast.Name):
                continue

            if not expr.func.id == 'run_shell':
                continue

            new_expr = ast.Call(
                func=ast.Name(id='print', ctx=ast.Load()),
                args=[expr],
                keywords=[],
            )
            statement.value = new_expr

    ast.fix_missing_locations(module)

    exec(compile(module, filename, mode='exec'))
