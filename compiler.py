import ast
import sys
import pickle
import pickletools
from helper import *
from tokenize import generate_tokens


class Compiler:
    def __init__(self, source):
        self.source = source
        self.bytecode = bytes()
        self.memo_manager = MemoManager()

    def compile(self):
        tree = ast.parse(self.source)
        if __import__('os').getenv("DEBUG"):
            kwargs = {'indent': 4} if sys.version_info >= (3, 9) else {}
            print(ast.dump(tree, **kwargs))
        for node in tree.body:
            self.traverse(node)

        if self.bytecode == b'':
            self.bytecode += pickle.NONE
        self.bytecode += pickle.STOP
        self.bytecode = pickletools.optimize(self.bytecode)

    def find_class(self, modname, name):
        if self.memo_manager.contains((modname, name)):
            self.fetch_memo((modname, name))
        else:
            self.bytecode += f'c{modname}\n{name}\n'.encode()

            # cache imported function / class to memo
            # if it is only used once, these bytecode will be removed by `pickletools.optimize` later
            if modname == '__builtin__':
                self.put_memo(name)
            else:
                self.put_memo((modname, name))

    def fetch_memo(self, key):
        index = self.memo_manager.get_memo(key).index
        if index <= 0xff:
            self.bytecode += pickle.BINGET + index.to_bytes(1, 'little')
        else:
            self.bytecode += pickle.LONG_BINGET + index.to_bytes(4, 'little')

    def put_memo(self, name):
        index = self.memo_manager.get_memo(name).index
        if index <= 0xff:
            self.bytecode += pickle.BINPUT + index.to_bytes(1, 'little')
        else:
            self.bytecode += pickle.LONG_BINPUT + index.to_bytes(4, 'little')
        # self.bytecode += pickle.PUT + str(index).encode() + b'\n'

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
            for target in targets:
                # TODO: unpacking assignment
                target_type = type(target)
                if target_type == ast.Name:
                    self.traverse(value)
                    self.put_memo(target.id)
                    self.bytecode += pickle.POP
                elif target_type == ast.Subscript:
                    # For `ITER[IDX] = NEW_VAL`:
                    self.traverse(target.value)  # get ITER
                    self.traverse(target.slice)  # IDX
                    self.traverse(value)  # NEW_VAL
                    self.bytecode += pickle.SETITEM
                elif target_type == ast.Attribute:
                    # For `OBJ.ATTR = VAL`:
                    self.traverse(target.value)  # get OBJ
                    self.bytecode += pickle.MARK

                    # BUILD arg 1: {}
                    self.bytecode += pickle.EMPTY_DICT

                    # BUILD arg 2: {attr: val}
                    self.bytecode += pickle.MARK
                    self.traverse(ast.Constant(target.attr))  # ATTR
                    self.traverse(value)  # VAL
                    self.bytecode += pickle.DICT

                    self.bytecode += pickle.TUPLE + pickle.BUILD
                else:
                    raise PickoraNotImplementedError(
                        f"{type(target).__name__} assignment", node, self.source)

        elif node_type == ast.Name:
            if self.memo_manager.contains(node.id):
                self.fetch_memo(node.id)
            elif is_builtins(node.id):
                self.find_class('__builtin__', node.id)
            else:
                raise PickoraNameError(f"name '{node.id}' is not defined.", node, self.source)

        elif node_type == ast.Expr:
            self.traverse(node.value)

        elif node_type == ast.Call:
            self.call_function(node.func, node.args)

        elif node_type == ast.Constant:
            val = node.value
            const_type = type(val)

            if const_type == int:
                if 0 <= val <= 0xff:
                    self.bytecode += pickle.BININT1 + val.to_bytes(1, 'little')
                elif 0 <= val <= 0xffff:
                    self.bytecode += pickle.BININT2 + val.to_bytes(2, 'little')
                elif -0x80000000 <= val <= 0x7fffffff:
                    self.bytecode += pickle.BININT + val.to_bytes(4, 'little', signed=True)
                else:
                    self.bytecode += pickle.INT + str(val).encode() + b'\n'
            elif const_type == float:
                self.bytecode += pickle.FLOAT + str(val).encode() + b'\n'
            elif const_type == bool:
                self.bytecode += pickle.NEWTRUE if val else pickle.NEWFALSE
            elif const_type == str:
                encoded = val.encode('utf-8', 'surrogatepass')
                n = len(encoded)
                self.bytecode += (pickle.SHORT_BINUNICODE + n.to_bytes(1, 'little')
                                  if n <= 0xff
                                  else pickle.BINUNICODE + n.to_bytes(4, 'little')) + encoded
            elif const_type == bytes:
                n = len(val)
                self.bytecode += (pickle.SHORT_BINBYTES + n.to_bytes(1, 'little')
                                  if n <= 0xff
                                  else pickle.BINBYTES + n.to_bytes(4, 'little')) + node.value
            elif val == None:
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

        # compatible with Python 3.8
        elif node_type == ast.Index:
            self.traverse(node.value)

        elif node_type == ast.Slice:
            self.call_function(('__builtin__', 'slice'), (node.lower, node.upper, node.step))

        elif node_type == ast.Attribute:
            self.call_function(('__builtin__', 'getattr'), (node.value, node.attr))

        elif node_type == ast.ImportFrom:
            for alias in node.names:
                self.find_class(node.module, alias.name)
                if getattr(alias, 'asname') != None:
                    self.put_memo(alias.asname)
                else:
                    self.put_memo(alias.name)

        elif node_type == ast.Import:
            for alias in node.names:
                self.call_function(('__builtin__', '__import__'), (alias.name, ))
                if getattr(alias, 'asname') != None:
                    self.put_memo(alias.asname)
                else:
                    self.put_memo(alias.name)

        else:
            raise PickoraNotImplementedError(node_type.__name__ + " syntax", node, self.source)
