import argparse
import pickle
import sys
import base64
from compiler import Compiler
from helper import PickoraError
import ast

if __name__ == "__main__":
    description = "A toy compiler that can convert Python scripts into pickle bytecode."
    epilog = "Basic usage: `python pickora.py samples/hello.py` or `python pickora.py -c 'print(\"Hello, world!\")' --extended`"
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("source", nargs="?", help="source code file")

    parser.add_argument("-c", "--code", help="source code string")
    parser.add_argument("-p", "--protocol", type=int,
                        default=pickle.DEFAULT_PROTOCOL, help="pickle protocol")
    parser.add_argument("-e", "--extended", action="store_true",
                        help="enable extended syntax (trigger find_class)")
    parser.add_argument("-O", "--optimize", action="store_true",
                        help="optimize pickle bytecode (with pickletools.optimize)")

    parser.add_argument("-o", "--output", help="output file")
    parser.add_argument("-d", "--disassemble",
                        action="store_true", help="disassemble pickle bytecode")
    parser.add_argument("-r", "--run", action="store_true",
                        help="run (load) pickle bytecode immediately")
    parser.add_argument("-f", "--format",
                        choices=["repr", "raw", "hex", "base64", "none"], default="repr", help="output format, none means no output")

    args = parser.parse_args()

    if args.source and args.code:
        parser.error("You can only specify one of source code file or string.")

    if args.source:
        with open(args.source, "r") as f:
            source = f.read()
    elif args.code:
        source = args.code
    else:
        parser.error("You must specify source code file or string.")

    compiler = Compiler(protocol=args.protocol,
                        optimize=args.optimize, extended=args.extended)

    try:
        code = compiler.compile(source, args.source)
    except PickoraError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if args.disassemble:
        import pickletools
        try:
            pickletools.dis(code)
        except Exception as e:
            print("[x] Disassemble error:", e, file=sys.stderr)

    if args.output:
        with open(args.output, "wb") as f:
            f.write(code)
    else:
        if args.format == "repr":
            print(repr(code))
        elif args.format == "raw":
            print(code.decode('latin1'), end="")
        elif args.format == "hex":
            print(code.hex())
        elif args.format == "base64":
            print(base64.b64encode(code).decode())
        elif args.format == "none":
            pass

    if args.run:
        print("[*] Running pickle bytecode...")
        ret = pickle.loads(code)
        print("[*] Return value:", repr(ret))
