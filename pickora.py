import pickle
from compiler import Compiler

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="the Python script to compile")
    parser.add_argument("-d", "--dis", help="disassamble the pickle output", action="store_true")
    parser.add_argument("-r", "--eval", help="run the pickle output", action="store_true")
    parser.add_argument("-o", "--output", type=str, help="Write output pickle to file")
    args = parser.parse_args()

    source = open(args.file, 'rb').read()
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
