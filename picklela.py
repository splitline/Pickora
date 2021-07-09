import ast
import pickle
from memo import Memo, MemoManager


def is_builtins(name):
    return name in __builtins__.__dir__()


pickle_res = b''
memo_manager = MemoManager()


def traverse(node):
    global pickle_res

    node_type = type(node)

    if node_type == ast.Assign:
        targets, value = node.targets, node.value
        traverse(value)
        for target in targets:
            memo = memo_manager.get_memo(target.id)
            pickle_res += pickle.PUT
            pickle_res += str(memo.index).encode() + b'\n'
        print(targets, value)

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
        traverse(node.func)
        pickle_res += pickle.MARK
        for arg in node.args:
            traverse(arg)
        pickle_res += pickle.TUPLE + pickle.REDUCE

    elif node_type == ast.Constant:
        if type(node.value) == int:
            pickle_res += pickle.INT + str(node.value).encode() + b'\n'
        elif type(node.value) == float:
            pickle_res += pickle.FLOAT + str(node.value).encode() + b'\n'
        elif type(node.value) == str:
            pickle_res += pickle.UNICODE + node.value.encode('unicode_escape') + b'\n'

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


if __name__ == "__main__":
    source = '''
math = __import__("math")
base = 2
exp = 10
res = pow(base, exp)
print(base, "**", exp, "=", res)
print(list(map(hex,[pow(2, 8), pow(2,16), pow(2,32)])))
print(getattr(math, 'pi'))
'''
    DEBUG = True

    tree = ast.parse(source)
    if DEBUG:
        print(ast.dump(tree, indent=4))

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
