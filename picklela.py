import ast
import pickle
from memo import Memo, MemoManager

def is_builtins(name):
    return name in __builtins__.__dir__()


pickle_res = b''


def traverse(stmt):
    global pickle_res

    stmt_type = type(stmt)

    if stmt_type == ast.Assign:
        targets, value = stmt.targets, stmt.value
        print(targets, value)
        # TODO

    elif stmt_type == ast.Expr:
        traverse(stmt.value)

    elif stmt_type == ast.Call:
        function_name, args = stmt.func.id, stmt.args
        if is_builtins(function_name):
            pickle_res += b'c__builtin__\n' + function_name.encode() + b'\n'
        else:
            raise NotImplementedError(f"Not a builtin function: {function_name}")

        pickle_res += pickle.MARK
        for arg in args:
            traverse(arg)
        pickle_res += pickle.TUPLE + pickle.REDUCE

    elif stmt_type == ast.Constant:
        if type(stmt.value) == int:
            pickle_res += pickle.INT + str(stmt.value).encode() + b'\n'
        elif type(stmt.value) == float:
            pickle_res += pickle.FLOAT + str(stmt.value).encode() + b'\n'
        elif type(stmt.value) == str:
            pickle_res += pickle.UNICODE + stmt.value.encode('unicode_escape') + b'\n'
            
    elif stmt_type == ast.List:
        pickle_res += pickle.MARK
        pickle_res += pickle.LIST
        for element in stmt.elts:
            traverse(element)
            pickle_res += pickle.APPEND

    elif stmt_type == ast.Dict:
        pickle_res += pickle.MARK
        pickle_res += pickle.DICT
        assert(len(stmt.keys) == len(stmt.values))
        for key, val in zip(stmt.keys, stmt.values):
            traverse(key)
            traverse(val)
            pickle_res += pickle.SETITEM

    elif stmt_type == ast.Attribute:
        # TODO
        pass


if __name__ == "__main__":
    source = '''
print("string", { 1337: "l33t", "int": 123, "float": 3.14, "nested": [{"x": "y", "list": [1,2,3]}, {"a":"b"}] })

''' 
    DEBUG = True

    tree = ast.parse(source)
    if DEBUG:
        print(ast.dump(tree, indent=2))

    for stmt in tree.body:
        traverse(stmt)

    pickle_res += pickle.STOP

    if DEBUG:
        import pickletools
        try:
            pickletools.dis(pickle_res)
        except:
            pass


    print("pickle:", pickle_res)
    pickle.loads(pickle_res)

