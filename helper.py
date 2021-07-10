import builtins
import ast

class PickoraError(Exception): pass

class PickoraNameError(PickoraError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PickoraNotImplementedError(PickoraError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Memo():
    def __init__(self, index, is_module=False):
        self.index = index


class MemoManager:
    def __init__(self):
        self.name_to_memo = {}
        self.current_index = 0

    def contains(self, name) -> bool:
        return name in self.name_to_memo

    def get_memo(self, name, is_module=False) -> Memo:
        if name in self.name_to_memo:
            return self.name_to_memo[name]

        self.name_to_memo[name] = Memo(self.current_index, is_module)
        self.current_index += 1
        return self.name_to_memo[name]


def is_builtins(name):
    return name in builtins.__dir__()


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
