import ast
import pickle
from helper import MemoManager


def is_builtins(name):
    return name in __builtins__.__dir__()


bytecode = b''
memo_manager = MemoManager()


def init_builtin_memos():
    def put_memo(name, index):
        global bytecode
        bytecode += b'c__builtin__\n' + name.encode() + b'\n'
        bytecode += pickle.PUT
        bytecode += str(index).encode() + b'\n'

    for name in ['getattr', '__import__']:
        put_memo(name, memo_manager.get_memo(name).index)


def traverse(node):
    global bytecode

    node_type = type(node)
    if node_type == ast.Assign:
        targets, value = node.targets, node.value
        traverse(value)
        for target in targets:
            memo = memo_manager.get_memo(target.id)
            bytecode += pickle.PUT
            bytecode += str(memo.index).encode() + b'\n'

    elif node_type == ast.Name:
        if memo_manager.contains(node.id):
            memo = memo_manager.get_memo(node.id)
            bytecode += pickle.GET
            bytecode += str(memo.index).encode() + b'\n'
        elif is_builtins(node.id):
            bytecode += b'c__builtin__\n' + node.id.encode() + b'\n'
        else:
            raise NameError(f"name '{node.id}' is not defined.")

    elif node_type == ast.Expr:
        traverse(node.value)

    elif node_type == ast.Call:
        func, args = node.func, node.args
        traverse(func)
        bytecode += pickle.MARK
        for arg in args:
            traverse(arg)
        bytecode += pickle.TUPLE + pickle.REDUCE

    elif node_type == ast.Constant:
        if type(node.value) == int:
            bytecode += pickle.INT + str(node.value).encode() + b'\n'
        elif type(node.value) == float:
            bytecode += pickle.FLOAT + str(node.value).encode() + b'\n'
        elif type(node.value) == str:
            bytecode += pickle.UNICODE + node.value.encode('unicode_escape') + b'\n'
        elif type(node.value) == bool:
            bytecode += pickle.NEWTRUE if node.value else pickle.NEWFALSE
        elif type(node.value) == bytes:
            bytecode += pickle.BINBYTES + len(node.value).to_bytes(4, 'little') + node.value
        elif node.value == None:
            bytecode += pickle.NONE
        else:
            raise NotImplementedError(type(node.value))

    elif node_type == ast.List:
        bytecode += pickle.MARK
        bytecode += pickle.LIST
        for element in node.elts:
            traverse(element)
            bytecode += pickle.APPEND

    elif node_type == ast.Dict:
        bytecode += pickle.MARK
        bytecode += pickle.DICT
        assert(len(node.keys) == len(node.values))
        for key, val in zip(node.keys, node.values):
            traverse(key)
            traverse(val)
            bytecode += pickle.SETITEM

    elif node_type == ast.Attribute:
        traverse(ast.Name(id='getattr', ctx=ast.Load()))
        bytecode += pickle.MARK
        traverse(node.value)
        traverse(ast.Constant(value=node.attr))
        bytecode += pickle.TUPLE + pickle.REDUCE

    elif node_type == ast.ImportFrom:
        for alias in node.names:
            bytecode += f'c{node.module}\n{alias.name}\n'.encode()
            memo = memo_manager.get_memo(alias.name)
            bytecode += pickle.PUT
            bytecode += str(memo.index).encode() + b'\n'

    elif node_type == ast.Import:
        # We don't need to really import a module
        # for alias in node.names:
        #     call_function('__import__', [alias.name])
        #     memo = memo_manager.get_memo(alias.name)
        #     bytecode += pickle.PUT
        #     bytecode += str(memo.index).encode() + b'\n'
        pass

    else:
        raise NotImplementedError(node_type)


if __name__ == "__main__":
    source = open("test_source.py", 'rb').read()
    DEBUG = True
    tree = ast.parse(source)
    if DEBUG:
        print(ast.dump(tree, indent=4))

    init_builtin_memos()
    for node in tree.body:
        traverse(node)

    bytecode += pickle.STOP

    if DEBUG:
        import pickletools
        try:
            # pickletools.dis(bytecode)
            pass
        except:
            pass

    print("pickle:", bytecode)
    pickle.loads(bytecode)
