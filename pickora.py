import pickle
import sys
from compiler import Compiler
from helper import PikoraError


def excepthook(etype, value, tb):
    if isinstance(value, PikoraError):
        message, node, source = value.args
        print("Compile error:")
        print(" "+str(node.lineno).rjust(4) + " | " +
              source.splitlines()[node.lineno-1])
        print(" "*8+" "*node.col_offset + (node.end_col_offset-node.col_offset)*"^")
        print(" "*4+f"{etype.__name__}: {message}")
    else:
        from traceback import print_exception
        print_exception(etype, value, tb)


sys.excepthook = excepthook

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="A toy compiler that can convert Python scripts to pickle bytecode.")
    parser.add_argument("file", help="the Python script to compile")
    parser.add_argument("-d", "--dis", help="disassamble compiled pickle bytecode", action="store_true")
    parser.add_argument("-r", "--eval", "--run", help="run the pickle bytecode", action="store_true")
    parser.add_argument("-o", "--output", type=str, help="Write compiled pickle to file")
    args = parser.parse_args()

    source = open(args.file, 'r').read()
    compiler = Compiler(source)

    compiler.compile()
    bytecode = compiler.bytecode

    if args.dis:
        import pickletools
        try:
            pickletools.dis(bytecode)
            pass
        except:
            pass

    if args.output:
        print("Saving pickle to", args.output)
        with open(args.output, 'wb') as out:
            out.write(bytecode)
    else:
        print("Pickle =", bytecode)

    if args.eval:
        pickle.loads(bytecode)
