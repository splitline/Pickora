import argparse
import pickle
import sys
from compiler import Compiler
from helper import PickoraError
import ast


def excepthook(etype, value, tb):
    if isinstance(value, PickoraError):
        try:
            message, node, source = value.args
            print("Compile error:")
            print(" "+str(node.lineno).rjust(4) + " | " +
                  source.splitlines()[node.lineno-1])
            print(" "*8+" "*node.col_offset + (node.end_col_offset-node.col_offset)*"^")
            print(" "*4+f"{etype.__name__}: {message}")
        except:
            from traceback import print_exception
            print_exception(etype, value, tb)
    else:
        from traceback import print_exception
        print_exception(etype, value, tb)


sys.excepthook = excepthook

if __name__ == "__main__":
    description = "A toy compiler that can convert Python scripts to pickle bytecode."
    epilog = "Documentation can be found at https://github.com/splitline/Pickora"
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("file", help="the Python script to compile")
    parser.add_argument("-d", "--dis",
                        help="disassamble compiled pickle bytecode", action="store_true")
    parser.add_argument("-r", "--eval", "--run",
                        help="run the pickle bytecode", action="store_true")
    parser.add_argument("-l", "--lambda", dest='compile_lambda',
                        help="choose lambda compiling mode",
                        choices=['none', 'python', 'pickle'], default='none')
    parser.add_argument("-o", "--output", type=str, help="write compiled pickle to file")
    args = parser.parse_args()

    compiler = Compiler(filename=args.file, compile_lambda=args.compile_lambda)
    bytecode = compiler.compile()

    if args.dis:
        try:
            import pickletools
            pickletools.dis(bytecode)
        except Exception as err:
            print("[x] Disassamble error:", err, end='\n\n')

    if args.output:
        with open(args.output, 'wb') as out:
            out.write(bytecode)
    else:
        print("pickle_bytecode =", bytecode)

    if args.eval:
        ret = pickle.loads(bytecode)
        print("[+] pickle.loads returns:", repr(ret))
