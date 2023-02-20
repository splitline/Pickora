import builtins
import ast
from functools import wraps
import types
from operator import attrgetter
from typing import Any
import pickle


class PickoraError(Exception):
    pass


class PickoraNameError(PickoraError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PickoraNotImplementedError(PickoraError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def is_builtins(name):
    return name in builtins.__dir__()


def extended(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.extended:
            return func(self, *args, **kwargs)
        else:
            raise PickoraError(
                "Extended mode is not enabled (add -e or --extended option)"
            )
    return wrapper


def macro(*args, **kwargs):
    proto = kwargs.get('proto', 0)

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.proto < proto:
                raise PickoraError(
                    f"Macro {func.__name__} requires protocol {proto} but current protocol is {self.proto}"
                )
            if len(args) != len(func.__annotations__):
                raise PickoraError(
                    f"Macro {func.__name__} expected {len(func.__annotations__)} arguments but only got {len(args)}"
                )

            # resolve ast.Constant
            _args = args

            args = [arg.value if type(arg) == ast.Constant else arg
                    for arg in args]

            for arg, arg_type in zip(args, func.__annotations__.values()):
                if arg_type == Any:
                    continue

                if not isinstance(arg, arg_type):
                    def args2str(args):
                        return ', '.join(map(attrgetter('__name__'), args))
                    expected = args2str(func.__annotations__.values())
                    provided = args2str(map(type, args))
                    raise PickoraError(
                        f"Macro {func.__name__} expected({expected}) but got({provided})"
                    )

            return func(self, *_args, **kwargs)
        wrapper.__macro__ = True
        return wrapper

    if 'proto' in kwargs:
        wrapped = decorator
        return wrapped
    else:
        wrapped = decorator(args[0])
        return wrapped


op_to_method = {
    # BinOp
    ast.Add: 'add',
    ast.Sub: 'sub',
    ast.Mult: 'mul',
    ast.Div: 'truediv',
    ast.FloorDiv: 'floordiv',
    ast.Mod: 'mod',
    ast.Pow: 'pow',
    ast.LShift: 'lshift',
    ast.RShift: 'rshift',
    ast.BitOr: 'or',
    ast.BitXor: 'xor',
    ast.BitAnd: 'and',
    ast.MatMult: 'matmul',

    # UnaryOp
    ast.Invert: 'inv',
    ast.Not: 'not_',
    ast.UAdd: 'pos',
    ast.USub: 'neg',

    # Compare
    ast.Eq: "eq",
    ast.NotEq: "ne",
    ast.Lt: "lt",
    ast.LtE: "le",
    ast.Gt: "gt",
    ast.GtE: "ge",
    ast.Is: "is_",
    ast.IsNot: "is_not",
    ast.In: "contains",
    # ast.NotIn: "",
    # TODO: operator module doensn't include `not in` method
}
