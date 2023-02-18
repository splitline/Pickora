import pickle
import pickletools
import ast
import io
import sys
from struct import pack
import types

from helper import PickoraError, PickoraNameError, PickoraNotImplementedError, op_to_method, extended, is_builtins, macro


class NodeVisitor(ast.NodeVisitor):
    def __init__(self, pickler, extended=False):
        self.pickler = pickler
        self.proto = pickler.proto
        self.memo = {}

        self.extended = extended

        self.current_node = None

    def is_macro(self, macro_name):
        return hasattr(self, macro_name) and getattr(getattr(self, macro_name), '__macro__', False)

    @macro
    def BUILD(self, inst: ast.AST, state: ast.AST, slotstate: ast.AST):
        self.visit(inst)
        self.visit(ast.Tuple(elts=(state, slotstate),))
        self.write(pickle.BUILD)

    @macro
    def STACK_GLOBAL(self, name: ast.AST, value: ast.AST):
        self.visit(name)
        self.visit(value)
        self.write(pickle.STACK_GLOBAL)

    @macro
    def GLOBAL(self, module: str, name: str):
        self.write(f'c{module.value}\n{name.value}\n'.encode())

    @macro
    def INST(self, module: str, name: str, args: ast.Tuple):
        self.write(pickle.MARK)
        for arg in args.elts:
            self.visit(arg)
        self.write(f'i{module.value}\n{name.value}\n'.encode())

    def visit_Constant(self, node):
        self.save(node.value)

    def visit_List(self, node):
        self.pickler.save_list(node.elts)

    def visit_Tuple(self, node):
        self.pickler.save_tuple(node.elts)

    def visit_Set(self, node):
        self.pickler.save_set(node.elts)

    def visit_Dict(self, node):
        self.pickler.save_dict({
            key: value for key, value in zip(node.keys, node.values)
        })

    def visit_Name(self, node):
        if node.id in self.memo:
            self.get(node.id)
        elif is_builtins(name=node.id):
            if not self.extended:
                raise PickoraError(
                    "For using builtins, extended mode must be enabled (add -e or --extended option)"
                )
            # auto import builtins
            self.find_class('builtins', node.id)
            self.put(node.id)
        else:
            raise PickoraNameError(f"Name '{node.id}' is not defined")

    def visit_NamedExpr(self, node):
        self.visit(node.value)
        self.put(node.target.id)

    def visit_Assign(self, node):
        targets, value = node.targets, node.value
        for target in targets:
            if isinstance(target, ast.Name):
                self.visit(value)
                self.put(target.id)
            elif isinstance(target, ast.Subscript):
                self.visit(target.value)
                self.visit(target.slice)
                self.visit(value)
                self.write(pickle.SETITEM)
            elif isinstance(target, ast.Attribute):
                # BUILD({}, {"attr": 1337})
                self.visit(target.value)
                self.write(pickle.EMPTY_DICT)
                self.pickler.save_dict({target.attr: value})
                self.write(pickle.TUPLE2 + pickle.BUILD)
            else:
                raise PickoraNotImplementedError(
                    f"Assigning to {type(target)} is not supported"
                )

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and self.is_macro(node.func.id):
            getattr(self, node.func.id)(*node.args)
            return

        self.visit(node.func)
        self.pickler.save_tuple(node.args)
        self.write(pickle.REDUCE)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.find_class(node.module, alias.name)
            if alias.asname is not None:
                self.put(alias.asname)
            else:
                self.put(alias.name)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Expr(self, node):
        self.visit(node.value)

    @extended
    def visit_Import(self, node):
        for alias in node.names:
            self.call("importlib", "import_module", alias.name)
            if alias.asname is not None:
                self.put(alias.asname)
            else:
                self.put(alias.name)

    # compatiblity with python 3.8
    def visit_Index(self, node):
        self.visit(node.value)

    @extended
    def visit_Subscript(self, node):
        self.call("operator", "getitem", node.value, node.slice)

    @extended
    def visit_Slice(self, node):
        self.call("builtins", "slice", node.lower, node.upper, node.step)

    @extended
    def visit_Attribute(self, node):
        self.call("builtins", "getattr", node.value, node.attr)

    @extended
    def visit_BinOp(self, node):
        self.call("operator", op_to_method[type(
            node.op)], node.left, node.right)

    @extended
    def visit_UnaryOp(self, node):
        self.call("operator", op_to_method[type(node.op)], node.operand)

    @extended
    def visit_BoolOp(self, node):
        # (a or b or c)     next(filter(truth, (a, b, c)), c)
        # (a and b and c)   next(filter(not_, (a, b, c)), c)
        bool_ops = {ast.Or: 'truth', ast.And: 'not_'}
        symbol = ('operator', bool_ops[type(node.op)])

        self.find_class(*symbol)
        self.put(symbol, pop=True)

        self.call('builtins', 'filter', ast.Name(id=symbol), node.values)
        self.put(f'filter_result_{id(node)}', pop=True)

        self.call('builtins', 'next', ast.Name(
            id=f'filter_result_{id(node)}'), node.values[-1])

    @extended
    def visit_Compare(self, node):
        self.write(pickle.MARK)
        left = node.left
        for op, right in zip(node.ops, node.comparators):
            self.call("operator", op_to_method[type(op)], left, right)
            left = right
        self.write(pickle.TUPLE)
        arg_id = str(id(node))
        self.put(arg_id, pop=True)
        self.call("builtins", "all", ast.Name(id=arg_id))

    @extended
    def visit_Lambda(self, node):
        code = compile(ast.Expression(body=node), '<lambda>', 'eval')
        lambda_code = next(filter(lambda x:
                                  isinstance(x, types.CodeType),
                                  code.co_consts))  # get code object
        code_attrs = ('argcount', 'posonlyargcount', 'kwonlyargcount', 'nlocals', 'stacksize', 'flags',
                      'code', 'consts', 'names', 'varnames', 'filename', 'name', 'firstlineno', 'lnotab')
        code_args = [getattr(lambda_code, f"co_{attr}") for attr in code_attrs]
        globals_dict = {k: ast.Name(id=k) for k in code_args[8]}  # co_names
        self.call("types", "CodeType", *code_args)
        self.put(f"lambda_({id(node)})", pop=True)
        self.call("types", "FunctionType",
                  ast.Name(id=f"lambda_({id(node)})"),
                  globals_dict,
                  None,
                  tuple(node.args.defaults))

    def find_class(self, module, name):
        if self.memo.get((module, name), None) is None:
            if self.proto >= 4:
                self.save(module)
                self.save(name)
                self.write(pickle.STACK_GLOBAL)
            elif self.proto >= 3:
                self.write(pickle.GLOBAL + bytes(module, "utf-8") +
                           b'\n' + bytes(name, "utf-8") + b'\n')
            else:
                self.write(pickle.GLOBAL + bytes(module, "ascii") +
                           b'\n' + bytes(name, "ascii") + b'\n')
            self.put((module, name))
        else:
            self.get((module, name))

    def call(self, module, name, *args):
        self.find_class(module, name)
        self.pickler.save_tuple(args)
        self.write(pickle.REDUCE)

    # memo related functions

    def put(self, name, pop=False):
        def op_put(idx):
            if self.pickler.bin:
                if idx < 256:
                    return pickle.BINPUT + pack("<B", idx)
                else:
                    return pickle.LONG_BINPUT + pack("<I", idx)
            else:
                return pickle.PUT + repr(idx).encode("ascii") + b'\n'

        def op_memoize():
            return pickle.MEMOIZE

        # assign to an existing name
        if name in self.memo:
            idx = self.memo[name]
            self.write(op_put(idx))

        # assign to a new name
        elif self.proto >= 4:
            self.memo[name] = len(self.memo)
            self.write(op_memoize())
        else:
            idx = len(self.memo)
            self.memo[name] = idx
            self.write(op_put(idx))

        if pop:
            self.write(pickle.POP)

    def get(self, name):
        idx = self.memo[name]
        self.write(self.pickler.get(idx))

    def visit(self, node):
        self.current_node = node

        if not hasattr(self, f"visit_{type(node).__name__}"):
            raise PickoraNotImplementedError(
                f"Pickora does not support {type(node).__name__} yet"
            )

        return super().visit(node)

    def save(self, obj):
        self.pickler.save(obj)

    def write(self, obj):
        self.pickler.write(obj)


# compile the source code into bytecode
class Compiler(pickle._Pickler):
    def __init__(self, protocol=pickle.DEFAULT_PROTOCOL, optimize=False, extended=False):
        self.opcodes = io.BytesIO()
        self.optimize = optimize

        super().__init__(self.opcodes, protocol)
        self.codegen = NodeVisitor(self, extended=extended)
        self.fast = True  # disable default memoization

    def compile(self, source, filename="<string>"):
        if not filename:
            filename = "<string>"

        if self.proto >= 2:
            self.write(pickle.PROTO + pack("<B", self.proto))
        if self.proto >= 4:
            self.framer.start_framing()
        try:
            self.codegen.visit(ast.parse(source))
        except PickoraError as e:
            # fetch the source from current node (full line)
            lineno = self.codegen.current_node.lineno
            colno = self.codegen.current_node.col_offset
            collen = self.codegen.current_node.end_col_offset - colno

            source = source.splitlines()[lineno - 1]
            error_message = f"File '{filename}', line {lineno}\n"
            error_message += f"{source}\n"
            error_message += " " * \
                (source.index(source.lstrip()) + colno) + "^"*collen + "\n\n"
            error_message += f"{e.__class__.__name__}: {e}"
            raise PickoraError(error_message) from e

        self.write(pickle.STOP)
        self.framer.end_framing()

        opcode = self.opcodes.getvalue()
        if self.optimize:
            return pickletools.optimize(opcode)
        return opcode

    def save(self, obj):
        if isinstance(obj, ast.AST):
            self.codegen.visit(obj)
        else:
            super().save(obj)
