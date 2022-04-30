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
    epilog = "Basic usage: `python pickora.py -f samples/hello.py` or `python pickora.py -c 'print(\"Hello, world!\")'`"
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("-f", "--file", help="the Python script to compile")
    parser.add_argument("-d", "--dis",
                        help="disassamble compiled pickle bytecode", action="store_true")
    parser.add_argument("-r", "--run",
                        help="run the compiled pickle bytecode", action="store_true")
    parser.add_argument("-l", "--lambda", dest='compile_lambda',
                        help="choose lambda compiling mode",
                        choices=['none', 'python', 'pickle'], default='none')
    parser.add_argument("-c", "--code", type=str, help="code passed in as a string")
    parser.add_argument("-o", "--output", type=str, help="write compiled pickle to file")
    parser.add_argument("--format", help="Convert pickle to what format", choices=['hex', 'base64'])
    args = parser.parse_args()

    if args.file:
        compiler = Compiler(filename=args.file, compile_lambda=args.compile_lambda)
        bytecode = compiler.compile()
    elif args.code:
        compiler = Compiler(source=args.code, compile_lambda=args.compile_lambda)
        bytecode = compiler.compile()
    else:
        parser.print_help()
        sys.exit(1)

    if args.dis:
        try:
            import pickletools
            pickletools.dis(bytecode)
        except Exception as err:
            print("[x] Disassamble error:", err, end='\n\n')

    out_bytecode = bytecode
    if args.format:
        if args.format == 'hex':
            out_bytecode = bytecode.hex()
        elif args.format == 'base64':
            out_bytecode = bytecode.decode('latin-1').encode('ascii', 'backslashreplace').decode()

    if args.output:
        with open(args.output, 'wb') as out:
            out.write(out_bytecode)
    else:
        print("pickle_bytecode =", out_bytecode)

    if args.run:
        ret = pickle.loads(bytecode)
        print("[+] pickle.loads returns:", repr(ret))
