import os
import base64
import string
from urllib.parse import quote

base = 2
exp = 10

print(base, "**", exp, "=", pow(base, exp))

mixed_dict = {"int": 1337, "float": 3.14, "str": "Meow 🐈",
              "bytes": b'\x01\x02qwq\xff', "list": [1, 2, 3, [4, 5, 6]]}

print(mixed_dict)
print(mixed_dict['list'])
print("Should be True:", (3 > 2 < 8 == 8 >= 8 <= 11) == True)

printable = string.printable
print("URL encoded =", quote(printable))
print("Base64 encoded =", base64.b64encode(printable.encode()).decode())
print("Ascii =", ",".join(map(str, map(ord, printable))))
print("slice(0, -1, 2) =", printable[0:-7:2])
print("os.popen('date') =", os.popen('date').read())
