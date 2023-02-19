# Pickora 🐰

A small compiler that can convert Python scripts to pickle bytecode. 

## Requirements

- Python 3.8+

No third-party modules are required.

## Quick Start

### Installation

**Using pip:**

```sh
$ pip install pickora
```

**From source:**

```sh
$ git clone https://github.com/splitline/Pickora.git
$ cd Pickora
$ python setup.py install
```

### Basic Usage

**Compile from a string:**

```sh
$ pickora -c 'from builtins import print; print("Hello, world!")' -o output.pkl
$ python -m pickle output.pkl # load the pickle bytecode
Hello, world!
None
```

**Compile from a file:**

```sh
$ echo 'from builtins import print; print("Hello, world!")' > hello.py
$ pickora hello.py # output compiled pickle bytecode to stdout directly
b'\x80\x04\x95(\x00\x00\x00\x00\x00\x00\x00\x8c\x08builtins\x8c\x05print\x93\x94\x94h\x01\x8c\rHello, world!\x85R.'
```

## Usage

```
usage: pickora [-h] [-c CODE] [-p PROTOCOL] [-e] [-O] [-o OUTPUT] [-d] [-r]
               [-f {repr,raw,hex,base64,none}]
               [source]

A toy compiler that can convert Python scripts into pickle bytecode.

positional arguments:
  source                source code file

optional arguments:
  -h, --help            show this help message and exit
  -c CODE, --code CODE  source code string
  -p PROTOCOL, --protocol PROTOCOL
                        pickle protocol
  -e, --extended        enable extended syntax (trigger find_class)
  -O, --optimize        optimize pickle bytecode (with pickletools.optimize)
  -o OUTPUT, --output OUTPUT
                        output file
  -d, --disassemble     disassemble pickle bytecode
  -r, --run             run (load) pickle bytecode immediately
  -f {repr,raw,hex,base64,none}, --format {repr,raw,hex,base64,none}
                        output format, none means no output

Basic usage: `pickora samples/hello.py` or `pickora --code 'print("Hello, world!")' --extended`
```

## Supported Syntax

### Basic Syntax (achived by only using `pickle` opcodes)
- Basic types: int, float, bytes, string, dict, list, set, tuple, bool, None
- Assignment: `val = dict_['x'] = obj.attr = 'meow'`
- Augmented assignment: `x += 1`
- Named assignment: `(x := 1337)`
- Unpacking: `a, b, c = 1, 2, 3`
- Function call: `f(arg1, arg2)`
  - Doesn't support keyword argument.
- Import
  - `from module import things` (directly using `STACK_GLOBALS` bytecode)
- Macros (see below for more details)
  - `STACK_GLOBAL`
  - `GLOBAL`
  - `INST`
  - `OBJ`
  - `NEWOBJ`
  - `NEWOBJ_EX`
  - `BUILD`


### Extended Syntax (enabled by `-e` / `--extended` option)
> Note: All extended syntaxes are implemented by importing other built-in modules. So with this option will trigger `find_class` when loading the pickle bytecode.

- Attributes: `obj.attr` (using `builtins.getattr` only when you need to "load" an attribute)
- Operators (using `operator` module)
  - Binary operators: `+`, `-`, `*`, `/` etc.
  - Unary operators: `not`, `~`, `+val`, `-val`
  - Compare: `0 < 3 > 2 == 2 > 1` (using `builtins.all` for chained comparing)
  - Subscript: `list_[1:3]`, `dict_['key']` (using `builtins.slice` for slice)
  - Boolean operators (using `builtins.next`, `builtins.filter`)
    - and: using `operator.not_`
    - or: using `operator.truth`
    - `(a or b or c)` -> `next(filter(truth, (a, b, c)), c)`
    - `(a and b and c)` -> `next(filter(not_, (a, b, c)), c)`
- Import
  - `import module` (using `importlib.import_module`)
- Lambda
  - `lambda x,y=1: x+y`
  - Using `types.CodeType` and `types.FunctionType`
  - [Known bug] If any global variables are changed after the lambda definition, the lambda function won't see those changes.


## Macros

There are currently 4 macros available: `STACK_GLOBAL`, `GLOBAL`, `INST` and `BUILD`.

### `STACK_GLOBAL(modname: Any, name: Any)`

**Example:**
```python
function_name = input("> ") # > system
func = STACK_GLOBAL('os', function_name) # <built-in function system>
func("date") # Tue Jan 13 33:33:37 UTC 2077
```

**Behaviour:**
1. PUSH modname
2. PUSH name
3. STACK_GLOBAL

### `GLOBAL(modname: str, name: str)`

**Example:**
```python
func = GLOBAL("os", "system") # <built-in function system>
func("date") # Tue Jan 13 33:33:37 UTC 2077
```

**Behaviour:**

Simply write this piece of bytecode: `f"c{modname}\n{name}\n"`

### `INST(modname: str, name: str, args: tuple[Any])`

**Example:**
```python
command = input("cmd> ") # cmd> date
INST("os", "system", (command,)) # Tue Jan 13 33:33:37 UTC 2077
```

Behaviour:
1. PUSH a MARK
2. PUSH `args` by order
3. Run this piece of bytecode: `f'i{modname}\n{name}\n'`

### `BUILD(inst: Any, state: Any, slotstate: Any)`

> `state` is for `inst.__setstate__(state)` and `slotstate` is for setting attributes.

**Example:**
```python
from collections import _collections_abc
BUILD(_collections_abc, None, {'__all__': ['ChainMap', 'Counter', 'OrderedDict']})
```

**Behaviour:**

1. PUSH `inst`
2. PUSH `(state, slotstate)` (tuple)
3. PUSH `BUILD`

## FAQ

### What is pickle?

[RTFM](https://docs.python.org/3/library/pickle.html).

### Why?

It's cool.

### Is it useful?

No, not at all, it's definitely useless.

### So, is this garbage?

Yep, it's cool garbage.

### Would it support syntaxes like `if` / `while` / `for` ?

No. All pickle can do is just simply define a variable or call a function, so this kind of syntax wouldn't exist.

But if you want to do things like:
```python
ans = input("Yes/No: ")
if ans == 'Yes':
  print("Great!")
elif ans == 'No':
  exit()
```
It's still achievable! You can rewrite your code like this:

```python
from functools import partial
condition = {'Yes': partial(print, 'Great!'), 'No': exit}
ans = input("Yes/No: ")
condition.get(ans, repr)()
```
ta-da!

For the loop syntax, you can try to use `map` / `starmap` /  `reduce` etc .

And yes, you are right, it's functional programming time!

