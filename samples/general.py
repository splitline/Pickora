import base64
from urllib.parse import quote

base = 2
exp = 10

print(base, "**", exp, "=", pow(base, exp))

mixed_dict = {"int": 1337, "float": 3.14, "str": "Meow 🐈",
              "bytes": b'\x01\x02qwq\xff', "list": [1, 2, 3, [4, 5, 6]]}

print(mixed_dict)

string = input("string: ")
print("URL encoded =", quote(string))
print("Base64 encode", base64.b64encode(string.encode()))
print("Ascii =", ",".join(map(str, map(ord, string))))
