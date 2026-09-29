from SymbolTable import DataType
from ast_nodes import (
    Const, Var, Assign, Print, BinOp,
    RelOp, Cast, Ternary
)
from type_rules import SemanticError, is_numeric, promote


def check_var(node, symbol_table, errors):
    symbol = symbol_table.getSymbol(node.name)

    if symbol is None:
        errors.append(
            SemanticError(
                f"undeclared variable '{node.name}'",
                node.lineno
            )
        )
        return None

    return symbol.getDataType()



def check_assign_stmt(node, symbol_table, errors):
    symbol = symbol_table.getSymbol(node.var.name)

    if symbol is None:
        errors.append(
            SemanticError(
                f"undeclared variable '{node.var.name}'",
                node.lineno
            )
        )
        return None

    expr_type = check_expr(node.expr, symbol_table, errors)

    if expr_type is None:
        return None

    target_type = symbol.getDataType()


    if target_type == expr_type:
        return target_type


    if target_type == DataType.DOUBLE and expr_type == DataType.INT:
        node.expr = Cast(
            DataType.DOUBLE,
            node.expr,
            node.expr.lineno
        )
        return target_type

    
    errors.append(
        SemanticError(
            f"cannot assign {expr_type} to {target_type}",
            node.lineno
        )
    )

    return None


def check_binop(node, symbol_table, errors):
    left_type = check_expr(node.left, symbol_table, errors)
    right_type = check_expr(node.right, symbol_table, errors)

    if left_type is None or right_type is None:
        return None

    
    if not is_numeric(left_type) or not is_numeric(right_type):
        errors.append(
            SemanticError(
                f"invalid operands for '{node.op}'",
                node.lineno
            )
        )
        return None

    result_type = promote(left_type, right_type)

    if result_type == DataType.DOUBLE:

        if left_type == DataType.INT:
            node.left = Cast(
                DataType.DOUBLE,
                node.left,
                node.left.lineno
            )

        if right_type == DataType.INT:
            node.right = Cast(
                DataType.DOUBLE,
                node.right,
                node.right.lineno
            )

    return result_type




def check_relop(node, symbol_table, errors):
    left_type = check_expr(node.left, symbol_table, errors)
    right_type = check_expr(node.right, symbol_table, errors)

    if left_type is None or right_type is None:
        return None



    if is_numeric(left_type) and is_numeric(right_type):

        result_type = promote(left_type, right_type)

        
        if result_type == DataType.DOUBLE:

            if left_type == DataType.INT:
                node.left = Cast(
                    DataType.DOUBLE,
                    node.left,
                    node.left.lineno
                )

            if right_type == DataType.INT:
                node.right = Cast(
                    DataType.DOUBLE,
                    node.right,
                    node.right.lineno
                )

    
        return DataType.INT

    

    if left_type == right_type:
        return DataType.INT



    errors.append(
        SemanticError(
            f"invalid operands for relational operator "
            f"'{node.op}': {left_type} and {right_type}",
            node.lineno
        )
    )

    return None



def check_cast(node, symbol_table, errors):
    expr_type = check_expr(node.expr, symbol_table, errors)

    if expr_type is None:
        return None

    target_type = node.target_type


    if expr_type == target_type:
        return target_type

    
    if is_numeric(expr_type) and is_numeric(target_type):
        return target_type

    
    if expr_type == DataType.CHAR and target_type == DataType.INT:
        return target_type


    if expr_type == DataType.INT and target_type == DataType.CHAR:
        return target_type

    errors.append(
        SemanticError(
            f"invalid cast from {expr_type} to {target_type}",
            node.lineno
        )
    )

    return None



def check_ternary(node, symbol_table, errors):

    cond_type = check_expr(
        node.cond,
        symbol_table,
        errors
    )

    then_type = check_expr(
        node.then_expr,
        symbol_table,
        errors
    )

    else_type = check_expr(
        node.else_expr,
        symbol_table,
        errors
    )

    if cond_type is None or then_type is None or else_type is None:
        return None



    if not is_numeric(cond_type):
        errors.append(
            SemanticError(
                "ternary condition must be numeric",
                node.cond.lineno
            )
        )

    

    if then_type == else_type:
        return then_type


    if is_numeric(then_type) and is_numeric(else_type):

        result_type = promote(then_type, else_type)

        if result_type == DataType.DOUBLE:

            if then_type == DataType.INT:
                node.then_expr = Cast(
                    DataType.DOUBLE,
                    node.then_expr,
                    node.then_expr.lineno
                )

            if else_type == DataType.INT:
                node.else_expr = Cast(
                    DataType.DOUBLE,
                    node.else_expr,
                    node.else_expr.lineno
                )

        return result_type


    errors.append(
        SemanticError(
            f"incompatible types in ternary expression: "
            f"{then_type} and {else_type}",
            node.lineno
        )
    )

    return None


def check_expr(node, symbol_table, errors):

    if isinstance(node, Const):
        return node.type

    if isinstance(node, Var):
        return check_var(
            node,
            symbol_table,
            errors
        )

    if isinstance(node, BinOp):
        return check_binop(
            node,
            symbol_table,
            errors
        )

    if isinstance(node, RelOp):
        return check_relop(
            node,
            symbol_table,
            errors
        )

    if isinstance(node, Cast):
        return check_cast(
            node,
            symbol_table,
            errors
        )

    if isinstance(node, Ternary):
        return check_ternary(
            node,
            symbol_table,
            errors
        )

    return None



def check_stmt(node, symbol_table, errors):

    if isinstance(node, Assign):
        return check_assign_stmt(
            node,
            symbol_table,
            errors
        )

    if isinstance(node, Print):
        return check_expr(
            node.expr,
            symbol_table,
            errors
        )

    return None


def check_program(program):

    errors = []

    for func in program.getFunctions():

        symbol_table = func.getLocalSymbolTable()

        for stmt in func.getStatementsAstList():

            check_stmt(
                stmt,
                symbol_table,
                errors
            )

    return errors
