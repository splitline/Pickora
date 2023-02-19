mod = 'builtins'
p = STACK_GLOBAL(mod, 'print')
d = {"a": 1, "b": 2}
BUILD(help, d, {"c": 3, "d": 4})
p(help.a, help.b, help.c, help.d)

GLOBAL('os', 'system')('date')
INST('os', 'system', ('cal',))
OBJ(p, (1, 2, 3))

# INST(mod, name, ('hello', 'world')) # should fail
# INST(mod, name) # should fail
# INST('builtins', 123, ('hello', )) # should fail
