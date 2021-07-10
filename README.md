# Pickora 🐰

A small compiler that can convert Python scripts to pickle bytecode. 

## Usage

```
usage: pickora.py [-h] [-d] [-r] [-o OUTPUT] file

positional arguments:
  file                  the Python script to compile

optional arguments:
  -h, --help            show this help message and exit
  -d, --dis             disassamble the pickle output
  -r, --eval            run the pickle bytecode
  -o OUTPUT, --output OUTPUT
                        Write output pickle to file
```

For exmple, you can run:

```sh
python pickora.py -d samples/hello.py -o output.pkl
```

to compile `samples/hello.py` and show the disassamble result of the compiled pickle bytecode. 

But it won't run the pickle for you. If you want you should add `-r` option, or run the following command after compile:

```sh
python -m pickle output.pkl
```

## Todos

- [x] Operators (<s>compare</s>, <s>unary</s>, <s>binary</s>, <s>subscript</s>)
- [ ] Unpacking assignment
- [ ] Augmented assignment
- [ ] Function call with kwargs
- [ ] Macros (directly using GLOBAL, OBJECT bytecodes)
- [ ] lambda / function (optional)

## FAQ

### What is pickle?

[RTFM](https://docs.python.org/3/library/pickle.html).

### Why?

It's cool.

### Is it useful?

No, not at all, it's definitely useless.

### So, is this a garbage?

Yep, a cool garbage.

