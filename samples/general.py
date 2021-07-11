import string
import base64 as b64
from urllib.parse import quote
from os import popen as run_cmd

base = 2
exp = 10

print("pow(%d, %d) = %d" % (base, exp, pow(base, exp)))

mixed_dict = {"int": 1337, "float": 3.14, "str": "Meow 🐈",
              "bytes": b'\x01\x02qwq\xff', "list": [1, 2, 3, [4, 5, 6]]}

print(mixed_dict)
print(mixed_dict['list'])
print("Should be True:", (3 > 2 < 8 == 8 >= 8 <= 11) == True)

printable = string.printable
print("URL encoded =", quote(printable))
print("Base64 encoded =", b64.b64encode(printable.encode()).decode())
print("Ascii =", ",".join(map(str, map(ord, printable))))
print("slice(0, -7, 2) =", printable[0:-7:2])
print("os.popen('date') =", run_cmd('date').read())


# assignment tests
l = [1, 2, 3, 4]
x = l[1] = y = z = 10
l[2] = a = b = c = 100
i = j = k = l[0] = 1000
print(l)
print(x, y, z)
print(a, b, c)
print(i, j, k)

l[0:3] = [9, 8, 7]
print(l)

d = {"x": 1, "y": 2, "z": 3}
k = 'y'
d[k] = 999
d['owo'] = 'new'
print(d)

string.my_str = 'meow 🐱'
print(string.my_str)

# lambda tests
print(list(map(lambda x, y: x+y, range(0, 10), range(100, 110))))
f = lambda a, b=pow(2, 2): a+b
print(f, f(5), f(5, 5))
