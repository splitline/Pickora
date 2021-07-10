import ast
import sys
import pickle
import pickletools
from helper import *


class Compiler:
    def __init__(self, source):
        self.source = source
        self.bytecode = bytes()
        self.memo_manager = MemoManager()

    def compile(self):
        tree = ast.parse(self.source)
        if __import__('os').getenv("DEBUG"):
            print(ast.dump(tree, indent=4))
        for node in tree.body:
            self.traverse(node)
        self.bytecode += pickle.STOP
        self.bytecode = pickletools.optimize(self.bytecode)

    def find_class(self, modname, name):
        if self.memo_manager.contains((modname, name)):
            memo = self.memo_manager.get_memo((modname, name))
            self.bytecode += pickle.GET
            self.bytecode += str(memo.index).encode() + b'\n'
        else:
            self.bytecode += f'c{modname}\n{name}\n'.encode()
            if modname == '__builtin__':
                self.put_memo(name)
            else:
                self.put_memo((modname, name))


    def put_memo(self, name):
        index = self.memo_manager.get_memo(name).index
        self.bytecode += pickle.PUT
        self.bytecode += str(index).encode() + b'\n'

    def call_function(self, func, args):
        if type(func) == tuple:
            self.find_class(*func)
        else:
            if type(func) == str:
                func = ast.Name(id=func, ctx=ast.Load())
            self.traverse(func)
        self.bytecode += pickle.MARK
        for arg in args:
            if not isinstance(arg, ast.AST):
                arg = ast.Constant(value=arg)
            self.traverse(arg)
        self.bytecode += pickle.TUPLE + pickle.REDUCE

    def traverse(self, node):
        node_type = type(node)
        if node_type == ast.Assign:
            targets, value = node.targets, node.value
            self.traverse(value)
            for target in targets:
                self.put_memo(target.id)

        elif node_type == ast.Name:
            if self.memo_manager.contains(node.id):
                memo = self.memo_manager.get_memo(node.id)
                self.bytecode += pickle.GET
                self.bytecode += str(memo.index).encode() + b'\n'
            elif is_builtins(node.id):
                self.find_class('__builtin__', node.id)
            else:
                raise PickoraNameError(f"name '{node.id}' is not defined.", node, self.source)

        elif node_type == ast.Expr:
            self.traverse(node.value)

        elif node_type == ast.Call:
            self.call_function(node.func, node.args)

        elif node_type == ast.Constant:
            if type(node.value) == int:
                self.bytecode += pickle.INT + str(node.value).encode() + b'\n'
            elif type(node.value) == float:
                self.bytecode += pickle.FLOAT + str(node.value).encode() + b'\n'
            elif type(node.value) == str:
                self.bytecode += pickle.UNICODE + node.value.encode('unicode_escape') + b'\n'
            elif type(node.value) == bool:
                self.bytecode += pickle.NEWTRUE if node.value else pickle.NEWFALSE
            elif type(node.value) == bytes:
                self.bytecode += pickle.BINBYTES + \
                    len(node.value).to_bytes(4, 'little') + node.value
            elif node.value == None:
                self.bytecode += pickle.NONE
            else:
                # I am not sure if there are types I didn't implement 🤔
                raise PickoraNotImplementedError("Type:", type(node.value))

        elif node_type == ast.Tuple:
            self.bytecode += pickle.MARK
            for element in node.elts:
                self.traverse(element)
            self.bytecode += pickle.TUPLE

        elif node_type == ast.List:
            self.bytecode += pickle.MARK
            self.bytecode += pickle.LIST
            for element in node.elts:
                self.traverse(element)
                self.bytecode += pickle.APPEND

        elif node_type == ast.Dict:
            self.bytecode += pickle.MARK
            self.bytecode += pickle.DICT
            assert(len(node.keys) == len(node.values))
            for key, val in zip(node.keys, node.values):
                self.traverse(key)
                self.traverse(val)
                self.bytecode += pickle.SETITEM

        elif node_type == ast.Compare:
            # a>b>c -> all((a>b, b>c))
            self.find_class("__builtin__", 'all')
            self.bytecode += pickle.MARK

            self.bytecode += pickle.MARK  # TUPLE mark
            left = node.left
            for _op, right in zip(node.ops, node.comparators):
                op = type(_op)
                assert(op in op_to_method)
                self.call_function(
                    ('operator', op_to_method.get(op)),
                    (left, right)
                )
                left = right
            self.bytecode += pickle.TUPLE  # /TUPLE

            self.bytecode += pickle.TUPLE + pickle.REDUCE

        # TODO: BoolOp
        elif node_type in [ast.BinOp, ast.UnaryOp]:
            op = type(node.op)
            assert(op in op_to_method)

            # # magic methods are really magic, I don't understand it well :(
            # self.getattr(node.left, '__'+op_to_method.get(op)+'__')
            args = tuple()
            if node_type == ast.BinOp:
                args = (node.left, node.right)
            elif node_type == ast.UnaryOp:
                args = (node.operand,)

            self.call_function(("operator", op_to_method.get(op)), args)

        elif node_type == ast.Subscript:
            self.call_function(('operator', "getitem"), (node.value, node.slice))

        elif node_type == ast.Slice:
            args = (node.lower, node.upper)
            if hasattr(node, 'step'):
                args += (node.step, )
            self.call_function(('__builtin__', 'slice'), args)

        elif node_type == ast.Attribute:
            self.call_function('getattr', (node.value, node.attr))

        elif node_type == ast.ImportFrom:
            for alias in node.names:
                self.find_class(node.module, alias.name)
                self.put_memo(alias.name)

        elif node_type == ast.Import:
            for alias in node.names:
                self.call_function('__import__', (alias.name, ))
                self.put_memo(alias.name)

        else:
            raise PickoraNotImplementedError(node_type.__name__ + " syntax", node, self.source)
