import ast
import pickle
from helper import MemoManager


def is_builtins(name):
    return name in __builtins__.__dir__()


pickle_res = b''
memo_manager = MemoManager()


def init_builtin_memos():
    def put_memo(name, index):
        global pickle_res
        pickle_res += b'c__builtin__\n' + name.encode() + b'\n'
        pickle_res += pickle.PUT
        pickle_res += str(index).encode() + b'\n'

    for name in ['getattr', '__import__']:
        put_memo(name, memo_manager.get_memo(name).index)


def traverse(node):
    global pickle_res

    def call_function(func, args):
        global pickle_res
        if type(func) == str:
            func = ast.Name(id=func, ctx=ast.Load())
        traverse(func)
        pickle_res += pickle.MARK
        for arg in args:
            if getattr(arg, '__module__', None) != 'ast':
                arg = ast.Constant(value=arg)
            traverse(arg)
        pickle_res += pickle.TUPLE + pickle.REDUCE

    node_type = type(node)
    if node_type == ast.Assign:
        targets, value = node.targets, node.value
        traverse(value)
        for target in targets:
            memo = memo_manager.get_memo(target.id)
            pickle_res += pickle.PUT
            pickle_res += str(memo.index).encode() + b'\n'

    elif node_type == ast.Name:
        if memo_manager.contains(node.id):
            memo = memo_manager.get_memo(node.id)
            pickle_res += pickle.GET
            pickle_res += str(memo.index).encode() + b'\n'
        elif is_builtins(node.id):
            pickle_res += b'c__builtin__\n' + node.id.encode() + b'\n'
        else:
            raise NameError(f"name '{node.id}' is not defined.")

    elif node_type == ast.Expr:
        traverse(node.value)

    elif node_type == ast.Call:
        call_function(node.func, node.args)

    elif node_type == ast.Constant:
        if type(node.value) == int:
            pickle_res += pickle.INT + str(node.value).encode() + b'\n'
        elif type(node.value) == float:
            pickle_res += pickle.FLOAT + str(node.value).encode() + b'\n'
        elif type(node.value) == str:
            pickle_res += pickle.UNICODE + node.value.encode('unicode_escape') + b'\n'
        elif type(node.value) == bool:
            pickle_res += pickle.NEWTRUE if node.value else pickle.NEWFALSE
        elif type(node.value) == bytes:
            pickle_res += pickle.BINBYTES + len(node.value).to_bytes(4, 'little') + node.value
        elif node.value == None:
            pickle_res += pickle.NONE
        else:
            raise NotImplementedError(type(node.value))

    elif node_type == ast.List:
        pickle_res += pickle.MARK
        pickle_res += pickle.LIST
        for element in node.elts:
            traverse(element)
            pickle_res += pickle.APPEND

    elif node_type == ast.Dict:
        pickle_res += pickle.MARK
        pickle_res += pickle.DICT
        assert(len(node.keys) == len(node.values))
        for key, val in zip(node.keys, node.values):
            traverse(key)
            traverse(val)
            pickle_res += pickle.SETITEM

    elif node_type == ast.Attribute:
        # TODO
        pass

    elif node_type == ast.ImportFrom:
        for alias in node.names:
            pickle_res += f'c{node.module}\n{alias.name}\n'.encode()
            memo = memo_manager.get_memo(alias.name)
            pickle_res += pickle.PUT
            pickle_res += str(memo.index).encode() + b'\n'

    elif node_type == ast.Import:
        # We don't really need to import modules
        pass
        # for alias in node.names:
        #     call_function('__import__', [alias.name])
        #     memo = memo_manager.get_memo(alias.name)
        #     pickle_res += pickle.PUT
        #     pickle_res += str(memo.index).encode() + b'\n'

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

    pickle_res += pickle.STOP

    if DEBUG:
        import pickletools
        try:
            pickletools.dis(pickle_res)
        except:
            pass

    print("pickle:", pickle_res)
    pickle.loads(pickle_res)
