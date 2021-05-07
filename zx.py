"""zxpy: Shell scripts made simple"""
import ast
import fileinput
import shlex
import subprocess


def cli() -> None:
    for line in fileinput.input():
        if line.lstrip().startswith('#'):
            continue

        if len(line.strip()) == 0:
            continue

        line_ast = ast.parse(line)
        statement = line_ast.body[0]
        if not isinstance(statement, (ast.Expr, ast.Assign)):
            print(f'Syntax curently unsupported: {line}')
            return

        expr = statement.value
        if (
            isinstance(expr, ast.UnaryOp)
            and isinstance(expr.op, ast.Invert)
            and isinstance(expr.operand, ast.Str)
        ):
            shell_command = expr.operand.value
            output = subprocess.getoutput(shell_command)

            if isinstance(statement, ast.Assign):
                variable = statement.targets[0]
                assert isinstance(variable, ast.Name)
                py_command = f'{variable.id} = {output}'
                exec(py_command)

            else:
                print(output)

        else:
            exec(line)
